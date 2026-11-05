#!/usr/bin/env python3
"""
chart_ontology.py — Módulo de consulta de ontología de gráficos para NEVEN

Este módulo proporciona funciones para:
1. Cargar el catálogo de gráficos desde los archivos YAML
2. Buscar gráficos por keywords (para RAG)
3. Recomendar gráficos basado en tipos de datos
4. Obtener implementaciones de código

Uso desde el agente:
    from scripts.ontology.chart_ontology import ChartOntology
    
    ontology = ChartOntology()
    results = ontology.search("correlación variables", lang="es")
    code = ontology.get_implementation("scatter-basic", "python", "matplotlib")
"""

import os
import re
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from functools import lru_cache

# Rutas por defecto - usar C:\NEVEN como base en producción
_NEVEN_ROOT = Path(os.environ.get("NEVEN_HOME", r"C:\NEVEN"))
DEFAULT_ONTOLOGY_PATH = _NEVEN_ROOT / "docs" / "ontologia" / "graficos"
DEFAULT_ANYPLOT_PATH = _NEVEN_ROOT / "external" / "anyplot"


@dataclass
class ChartMatch:
    """Resultado de búsqueda de gráfico"""
    id: str
    name: Dict[str, str]
    score: float
    use_when: Dict[str, List[str]]
    implementations: Dict[str, Dict[str, str]]
    data_requirements: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "score": self.score,
            "use_when": self.use_when,
            "implementations": self.implementations,
            "data_requirements": self.data_requirements
        }


class ChartOntology:
    """
    Gestiona la ontología de gráficos de NEVEN.
    Proporciona búsqueda semántica y recomendaciones basadas en datos.
    """
    
    def __init__(self, 
                 ontology_path: Optional[Path] = None,
                 anyplot_path: Optional[Path] = None):
        """
        Inicializa la ontología.
        
        Args:
            ontology_path: Ruta a los archivos YAML de ontología
            anyplot_path: Ruta al repositorio anyplot clonado
        """
        self.ontology_path = Path(ontology_path) if ontology_path else DEFAULT_ONTOLOGY_PATH
        self.anyplot_path = Path(anyplot_path) if anyplot_path else DEFAULT_ANYPLOT_PATH
        
        self._catalog: Dict[str, Dict] = {}
        self._keyword_index: Dict[str, List[str]] = {}  # keyword -> [chart_ids]
        self._loaded = False
    
    def load(self) -> int:
        """
        Carga todos los archivos de ontología.
        
        Returns:
            Número de gráficos cargados
        """
        if self._loaded:
            return len(self._catalog)
        
        if not self.ontology_path.exists():
            raise FileNotFoundError(f"Ontology path not found: {self.ontology_path}")
        
        # Cargar cada archivo YAML
        for yaml_file in self.ontology_path.glob("*.yaml"):
            if yaml_file.name.startswith("_"):
                continue  # Saltar _catalog.yaml
            
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    if data and "id" in data:
                        chart_id = data["id"]
                        self._catalog[chart_id] = data
                        
                        # Indexar keywords
                        self._index_keywords(chart_id, data)
            except Exception as e:
                print(f"Warning: Error loading {yaml_file}: {e}")
        
        self._loaded = True
        return len(self._catalog)
    
    def _index_keywords(self, chart_id: str, data: Dict):
        """Indexa keywords para búsqueda rápida"""
        keywords = set()
        
        # Keywords explícitos
        for lang in ["en", "es"]:
            if "keywords" in data and lang in data["keywords"]:
                keywords.update(kw.lower() for kw in data["keywords"][lang])
        
        # Aliases
        for lang in ["en", "es"]:
            if "aliases" in data and lang in data["aliases"]:
                keywords.update(alias.lower() for alias in data["aliases"][lang])
        
        # Tags
        if "tags" in data:
            for category, tags in data["tags"].items():
                if isinstance(tags, list):
                    keywords.update(tag.lower() for tag in tags)
        
        # Agregar al índice invertido
        for kw in keywords:
            if kw not in self._keyword_index:
                self._keyword_index[kw] = []
            if chart_id not in self._keyword_index[kw]:
                self._keyword_index[kw].append(chart_id)
    
    def search(self, 
               query: str, 
               lang: str = "es",
               limit: int = 5) -> List[ChartMatch]:
        """
        Busca gráficos por texto libre.
        
        Args:
            query: Texto de búsqueda (ej: "correlación entre variables")
            lang: Idioma ("es" o "en")
            limit: Máximo de resultados
            
        Returns:
            Lista de ChartMatch ordenados por relevancia
        """
        if not self._loaded:
            self.load()
        
        # Tokenizar query
        query_tokens = set(re.findall(r'\w+', query.lower()))
        
        # Calcular scores
        scores: Dict[str, float] = {}
        
        for token in query_tokens:
            # Búsqueda exacta
            if token in self._keyword_index:
                for chart_id in self._keyword_index[token]:
                    scores[chart_id] = scores.get(chart_id, 0) + 2.0
            
            # Búsqueda parcial (substring)
            for kw, chart_ids in self._keyword_index.items():
                if token in kw or kw in token:
                    for chart_id in chart_ids:
                        scores[chart_id] = scores.get(chart_id, 0) + 0.5
        
        # Ordenar por score
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)[:limit]
        
        # Construir resultados
        results = []
        for chart_id in sorted_ids:
            data = self._catalog[chart_id]
            results.append(ChartMatch(
                id=chart_id,
                name=data.get("name", {"en": chart_id, "es": chart_id}),
                score=scores[chart_id],
                use_when=data.get("use_when", {"en": [], "es": []}),
                implementations=data.get("implementations", {}),
                data_requirements=data.get("data_requirements", {})
            ))
        
        return results
    
    def recommend_by_data(self,
                          column_types: List[str],
                          num_columns: int,
                          num_rows: int,
                          lang: str = "es") -> List[ChartMatch]:
        """
        Recomienda gráficos basado en las características de los datos.
        
        Args:
            column_types: Lista de tipos de columna ("numeric", "categorical", "temporal")
            num_columns: Número de columnas
            num_rows: Número de filas
            lang: Idioma
            
        Returns:
            Lista de ChartMatch ordenados por idoneidad
        """
        if not self._loaded:
            self.load()
        
        scores: Dict[str, float] = {}
        
        # Normalizar tipos
        types_lower = [t.lower() for t in column_types]
        has_numeric = any("num" in t for t in types_lower)
        has_categorical = any("cat" in t for t in types_lower)
        has_temporal = any("temp" in t or "date" in t or "time" in t for t in types_lower)
        num_numeric = sum(1 for t in types_lower if "num" in t)
        
        for chart_id, data in self._catalog.items():
            score = 0.0
            reqs = data.get("data_requirements", {})
            
            # Verificar número de columnas
            min_cols = reqs.get("min_columns", 1)
            if num_columns >= min_cols:
                score += 1.0
            else:
                continue  # No cumple requisitos mínimos
            
            # Verificar tipos de columna
            req_types = reqs.get("column_types", [])
            if req_types:
                type_match = 0
                for req_type in req_types:
                    if "numeric" in req_type.lower() and has_numeric:
                        type_match += 1
                    elif "categorical" in req_type.lower() and has_categorical:
                        type_match += 1
                    elif "temporal" in req_type.lower() and has_temporal:
                        type_match += 1
                
                if type_match > 0:
                    score += type_match * 2.0
            
            # Verificar número de filas
            rec_rows = reqs.get("recommended_rows", {})
            min_rows = rec_rows.get("min", 1)
            max_rows = rec_rows.get("max", 1000000)
            if min_rows <= num_rows <= max_rows:
                score += 1.0
            
            # Bonus para gráficos comunes/básicos
            if "basic" in chart_id:
                score += 0.5
            
            if score > 0:
                scores[chart_id] = score
        
        # Ordenar y retornar top 5
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)[:5]
        
        results = []
        for chart_id in sorted_ids:
            data = self._catalog[chart_id]
            results.append(ChartMatch(
                id=chart_id,
                name=data.get("name", {"en": chart_id, "es": chart_id}),
                score=scores[chart_id],
                use_when=data.get("use_when", {"en": [], "es": []}),
                implementations=data.get("implementations", {}),
                data_requirements=data.get("data_requirements", {})
            ))
        
        return results
    
    def get_chart(self, chart_id: str) -> Optional[Dict]:
        """
        Obtiene los datos completos de un gráfico.
        
        Args:
            chart_id: ID del gráfico (ej: "scatter-basic")
            
        Returns:
            Diccionario con todos los datos del gráfico, o None
        """
        if not self._loaded:
            self.load()
        
        return self._catalog.get(chart_id)
    
    def get_implementation(self, 
                           chart_id: str, 
                           language: str, 
                           library: str) -> Optional[str]:
        """
        Obtiene el código de implementación de un gráfico.
        
        Args:
            chart_id: ID del gráfico
            language: Lenguaje ("python", "r", "julia", "javascript")
            library: Librería ("matplotlib", "ggplot2", etc.)
            
        Returns:
            Código fuente como string, o None si no existe
        """
        if not self._loaded:
            self.load()
        
        chart = self._catalog.get(chart_id)
        if not chart:
            return None
        
        impls = chart.get("implementations", {})
        if language not in impls:
            return None
        
        if library not in impls[language]:
            return None
        
        # Construir ruta al archivo
        rel_path = impls[language][library]
        full_path = self.anyplot_path / rel_path
        
        if not full_path.exists():
            return None
        
        try:
            return full_path.read_text(encoding='utf-8')
        except Exception:
            return None
    
    def list_all(self, lang: str = "es") -> List[Dict[str, str]]:
        """
        Lista todos los gráficos disponibles.
        
        Args:
            lang: Idioma para los nombres
            
        Returns:
            Lista de {id, name} para todos los gráficos
        """
        if not self._loaded:
            self.load()
        
        return [
            {
                "id": chart_id,
                "name": data.get("name", {}).get(lang, chart_id)
            }
            for chart_id, data in sorted(self._catalog.items())
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del catálogo"""
        if not self._loaded:
            self.load()
        
        # Contar implementaciones por lenguaje
        lang_counts: Dict[str, int] = {}
        lib_counts: Dict[str, int] = {}
        
        for data in self._catalog.values():
            for lang, libs in data.get("implementations", {}).items():
                lang_counts[lang] = lang_counts.get(lang, 0) + 1
                for lib in libs.keys():
                    lib_counts[lib] = lib_counts.get(lib, 0) + 1
        
        return {
            "total_charts": len(self._catalog),
            "total_keywords": len(self._keyword_index),
            "by_language": lang_counts,
            "by_library": lib_counts
        }


# ============================================================================
# CLI para pruebas
# ============================================================================

if __name__ == "__main__":
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="Chart Ontology CLI")
    parser.add_argument("command", choices=["search", "recommend", "get", "stats", "list"])
    parser.add_argument("--query", "-q", help="Search query")
    parser.add_argument("--id", help="Chart ID")
    parser.add_argument("--lang", default="es", help="Language (es/en)")
    parser.add_argument("--types", nargs="+", help="Column types for recommend")
    parser.add_argument("--cols", type=int, default=2, help="Number of columns")
    parser.add_argument("--rows", type=int, default=100, help="Number of rows")
    args = parser.parse_args()
    
    ontology = ChartOntology()
    
    if args.command == "search":
        if not args.query:
            print("Error: --query required for search")
            exit(1)
        results = ontology.search(args.query, lang=args.lang)
        for r in results:
            print(f"[{r.score:.1f}] {r.id}: {r.name[args.lang]}")
    
    elif args.command == "recommend":
        types = args.types or ["numeric", "numeric"]
        results = ontology.recommend_by_data(types, args.cols, args.rows, args.lang)
        for r in results:
            print(f"[{r.score:.1f}] {r.id}: {r.name[args.lang]}")
    
    elif args.command == "get":
        if not args.id:
            print("Error: --id required for get")
            exit(1)
        chart = ontology.get_chart(args.id)
        if chart:
            print(json.dumps(chart, indent=2, ensure_ascii=False))
        else:
            print(f"Chart not found: {args.id}")
    
    elif args.command == "stats":
        stats = ontology.get_stats()
        print(json.dumps(stats, indent=2))
    
    elif args.command == "list":
        charts = ontology.list_all(args.lang)
        for c in charts[:20]:
            print(f"{c['id']}: {c['name']}")
        print(f"... and {len(charts) - 20} more")
