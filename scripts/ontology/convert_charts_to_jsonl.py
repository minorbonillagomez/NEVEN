#!/usr/bin/env python3
"""
convert_charts_to_jsonl.py — Convierte ontologías YAML de gráficos a formato JSONL para RAG

Este script lee los 326+ archivos YAML de gráficos en docs/ontologia/graficos/
y genera un archivo graph.jsonl compatible con el RAGEngine de NEVEN.

Formato de entrada (YAML):
    entity_type: ChartType
    id: scatter-basic
    name:
      en: Basic Scatter Plot
      es: Diagrama de Dispersión Básico
    description: {...}
    keywords: {...}
    ...

Formato de salida (JSONL):
    {"op": "create", "entity": {"id": "...", "type": "ChartType", "domain": "graficos", "properties": {...}}}

Uso:
    python convert_charts_to_jsonl.py [--input DIR] [--output FILE] [--lang LANG]

Autor: NEVEN Project
Fecha: 2026-08-19
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML no instalado. Ejecutar: pip install pyyaml")
    sys.exit(1)


# Configuración por defecto
DEFAULT_INPUT_DIR = Path(os.environ.get("NEVEN_HOME", r"C:\NEVEN")) / "docs" / "ontologia" / "graficos"
DEFAULT_OUTPUT_DIR = Path(os.environ.get("NEVEN_HOME", r"C:\NEVEN")) / "ontology" / "graficos"
DEFAULT_LANG = "es"  # Idioma principal para el RAG


def load_yaml_file(filepath: Path) -> Optional[Dict[str, Any]]:
    """Carga un archivo YAML de forma segura."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"  WARNING: Error cargando {filepath.name}: {e}")
        return None


def extract_localized_value(data: Any, lang: str, fallback_lang: str = "en") -> str:
    """Extrae valor localizado de un campo bilingüe."""
    if data is None:
        return ""
    if isinstance(data, str):
        return data
    if isinstance(data, dict):
        return data.get(lang) or data.get(fallback_lang) or str(next(iter(data.values()), ""))
    if isinstance(data, list):
        # Lista de strings o lista de dicts
        result = []
        for item in data:
            if isinstance(item, str):
                result.append(item)
            elif isinstance(item, dict):
                result.append(item.get(lang) or item.get(fallback_lang) or "")
        return "; ".join(filter(None, result))
    return str(data)


def extract_localized_list(data: Any, lang: str, fallback_lang: str = "en") -> List[str]:
    """Extrae lista de valores localizados."""
    if data is None:
        return []
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        items = data.get(lang) or data.get(fallback_lang) or []
        if isinstance(items, list):
            return items
        return [items] if items else []
    return [str(data)] if data else []


def convert_chart_to_entity(yaml_data: Dict[str, Any], lang: str) -> Optional[Dict[str, Any]]:
    """Convierte un YAML de gráfico al formato de entidad JSONL."""
    if not yaml_data:
        return None
    
    chart_id = yaml_data.get("id", "")
    if not chart_id:
        return None
    
    # Extraer campos localizados
    name = extract_localized_value(yaml_data.get("name"), lang)
    description = extract_localized_value(yaml_data.get("description"), lang)
    
    # Combinar use_when y applications como descripción extendida
    use_when = extract_localized_list(yaml_data.get("use_when"), lang)
    avoid_when = extract_localized_list(yaml_data.get("avoid_when"), lang)
    applications = extract_localized_list(yaml_data.get("applications"), lang)
    
    # Keywords para búsqueda
    keywords = extract_localized_list(yaml_data.get("keywords"), lang)
    aliases = extract_localized_list(yaml_data.get("aliases"), lang)
    
    # Combinar keywords, aliases, y nombre para mejor búsqueda
    all_keywords = list(set(keywords + aliases + [name.lower(), chart_id]))
    
    # Tags para categorización
    tags = yaml_data.get("tags", {})
    plot_types = tags.get("plot_type", [])
    domains = tags.get("domain", [])
    features = tags.get("features", [])
    
    # Requisitos de datos
    data_reqs = yaml_data.get("data_requirements", {})
    
    # Librerías disponibles
    implementations = yaml_data.get("implementations", {})
    available_libraries = []
    for lang_impl in implementations.values():
        if isinstance(lang_impl, dict):
            available_libraries.extend(lang_impl.keys())
    available_libraries = list(set(available_libraries))
    
    # Construir descripción enriquecida para el RAG
    full_description_parts = [description] if description else []
    
    if use_when:
        full_description_parts.append("Usar cuando: " + "; ".join(use_when))
    
    if avoid_when:
        full_description_parts.append("Evitar cuando: " + "; ".join(avoid_when))
    
    if applications:
        full_description_parts.append("Aplicaciones: " + "; ".join(applications[:3]))  # Limitar
    
    if available_libraries:
        full_description_parts.append(f"Librerías: {', '.join(available_libraries[:8])}")
    
    full_description = " | ".join(full_description_parts)
    
    # Construir entidad en formato RAG
    entity = {
        "op": "create",
        "entity": {
            "id": f"chart_{chart_id}",
            "type": yaml_data.get("entity_type", "ChartType"),
            "domain": "graficos",
            "properties": {
                "name": name,
                "description": full_description,
                "chart_id": chart_id,
                "keywords": all_keywords,
                "plot_types": plot_types,
                "domains": domains,
                "features": features,
                "libraries": available_libraries,
                "min_columns": data_reqs.get("min_columns"),
                "column_types": data_reqs.get("column_types", []),
            }
        }
    }
    
    # Limpiar valores None
    entity["entity"]["properties"] = {
        k: v for k, v in entity["entity"]["properties"].items() 
        if v is not None and v != [] and v != ""
    }
    
    return entity


def convert_all_charts(input_dir: Path, output_file: Path, lang: str) -> Dict[str, Any]:
    """Convierte todos los YAMLs de gráficos a un archivo JSONL."""
    
    print(f"[convert_charts] Input:  {input_dir}")
    print(f"[convert_charts] Output: {output_file}")
    print(f"[convert_charts] Lang:   {lang}")
    
    if not input_dir.exists():
        print(f"ERROR: Directorio de entrada no existe: {input_dir}")
        return {"success": False, "error": "Input directory not found"}
    
    # Crear directorio de salida si no existe
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Encontrar todos los YAMLs (excepto _catalog.yaml)
    yaml_files = sorted([
        f for f in input_dir.glob("*.yaml") 
        if not f.name.startswith("_")
    ])
    
    print(f"[convert_charts] Encontrados {len(yaml_files)} archivos YAML")
    
    entities = []
    errors = []
    
    for yaml_file in yaml_files:
        yaml_data = load_yaml_file(yaml_file)
        if yaml_data:
            entity = convert_chart_to_entity(yaml_data, lang)
            if entity:
                entities.append(entity)
            else:
                errors.append(f"{yaml_file.name}: No se pudo convertir")
        else:
            errors.append(f"{yaml_file.name}: Error de carga")
    
    # Escribir JSONL
    with open(output_file, 'w', encoding='utf-8') as f:
        for entity in entities:
            f.write(json.dumps(entity, ensure_ascii=False) + "\n")
    
    print(f"[convert_charts] Generadas {len(entities)} entidades")
    if errors:
        print(f"[convert_charts] {len(errors)} errores:")
        for err in errors[:5]:
            print(f"  - {err}")
        if len(errors) > 5:
            print(f"  ... y {len(errors) - 5} más")
    
    # Estadísticas
    stats = {
        "success": True,
        "total_files": len(yaml_files),
        "entities_generated": len(entities),
        "errors": len(errors),
        "output_file": str(output_file),
        "output_size_kb": round(output_file.stat().st_size / 1024, 2) if output_file.exists() else 0
    }
    
    print(f"[convert_charts] Archivo generado: {stats['output_size_kb']} KB")
    
    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Convierte ontologías YAML de gráficos a formato JSONL para RAG"
    )
    parser.add_argument(
        "--input", "-i",
        type=Path,
        default=DEFAULT_INPUT_DIR,
        help=f"Directorio con YAMLs de gráficos (default: {DEFAULT_INPUT_DIR})"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=DEFAULT_OUTPUT_DIR / "graph.jsonl",
        help=f"Archivo JSONL de salida (default: {DEFAULT_OUTPUT_DIR / 'graph.jsonl'})"
    )
    parser.add_argument(
        "--lang", "-l",
        type=str,
        default=DEFAULT_LANG,
        choices=["es", "en"],
        help=f"Idioma principal para extracción (default: {DEFAULT_LANG})"
    )
    
    args = parser.parse_args()
    
    stats = convert_all_charts(args.input, args.output, args.lang)
    
    if stats["success"]:
        print("\n✓ Conversión completada exitosamente")
        print(f"  Entidades: {stats['entities_generated']}")
        print(f"  Archivo:   {stats['output_file']}")
    else:
        print(f"\n✗ Error: {stats.get('error', 'Unknown')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
