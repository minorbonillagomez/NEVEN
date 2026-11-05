#!/usr/bin/env python3
"""
chart_handlers.py — HTTP handlers para la ontología de gráficos

Este módulo proporciona funciones handler que pueden ser importadas
por neven_http_server.py para servir endpoints de gráficos.

Endpoints:
- GET  /api/charts                     → Lista todos los tipos de gráficos
- GET  /api/charts/search?q=...&lang=  → Busca gráficos por texto
- GET  /api/charts/recommend           → Recomienda gráficos por tipo de datos
- GET  /api/charts/{id}                → Obtiene datos de un gráfico
- GET  /api/charts/{id}/code?lang=&lib= → Obtiene código de implementación
- GET  /api/charts/stats               → Estadísticas del catálogo

Integración con servidor:
    from scripts.ontology.chart_handlers import ChartHandlers
    
    handlers = ChartHandlers()
    
    # En do_GET:
    if path.startswith('api/charts'):
        handlers.handle(self, path, query_params)
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from urllib.parse import parse_qs

# Importar ontología
from chart_ontology import ChartOntology


def _serialize_for_json(obj: Any) -> Any:
    """Convierte objetos no serializables a formatos JSON compatibles."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: _serialize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_serialize_for_json(item) for item in obj]
    return obj


class ChartHandlers:
    """
    Handlers HTTP para consulta de gráficos.
    Diseñado para integrarse con NEVENHandler.
    """
    
    def __init__(self, ontology_path: Optional[Path] = None):
        """
        Inicializa los handlers.
        
        Args:
            ontology_path: Ruta opcional al directorio de ontologías
        """
        self.ontology = ChartOntology(ontology_path=ontology_path)
        self._loaded = False
    
    def _ensure_loaded(self):
        """Carga la ontología si no está cargada"""
        if not self._loaded:
            self.ontology.load()
            self._loaded = True
    
    def handle_list(self, query_params: Dict[str, list]) -> Dict[str, Any]:
        """
        GET /api/charts — Lista todos los gráficos
        
        Query params:
            - lang: Idioma (es/en), default: es
            - limit: Máximo de resultados (default: all)
        
        Returns:
            {"status": "ok", "total": N, "charts": [...]}
        """
        self._ensure_loaded()
        
        lang = query_params.get("lang", ["es"])[0]
        limit = int(query_params.get("limit", ["0"])[0])
        
        charts = self.ontology.list_all(lang=lang)
        
        if limit > 0:
            charts = charts[:limit]
        
        return {
            "status": "ok",
            "total": len(charts),
            "charts": charts
        }
    
    def handle_search(self, query_params: Dict[str, list]) -> Dict[str, Any]:
        """
        GET /api/charts/search?q=correlación&lang=es
        
        Query params:
            - q: Texto de búsqueda (requerido)
            - lang: Idioma (es/en), default: es
            - limit: Máximo de resultados, default: 5
        
        Returns:
            {"status": "ok", "results": [...]}
        """
        self._ensure_loaded()
        
        query = query_params.get("q", [""])[0]
        if not query:
            return {"status": "error", "message": "Missing query parameter 'q'"}
        
        lang = query_params.get("lang", ["es"])[0]
        limit = int(query_params.get("limit", ["5"])[0])
        
        results = self.ontology.search(query, lang=lang, limit=limit)
        
        return {
            "status": "ok",
            "query": query,
            "lang": lang,
            "results": [r.to_dict() for r in results]
        }
    
    def handle_recommend(self, query_params: Dict[str, list]) -> Dict[str, Any]:
        """
        GET /api/charts/recommend?types=numeric,numeric&cols=2&rows=100
        
        Query params:
            - types: Tipos de columna separados por coma (numeric, categorical, temporal)
            - cols: Número de columnas
            - rows: Número de filas
            - lang: Idioma (es/en), default: es
        
        Returns:
            {"status": "ok", "recommendations": [...]}
        """
        self._ensure_loaded()
        
        types_str = query_params.get("types", ["numeric,numeric"])[0]
        types = [t.strip() for t in types_str.split(",")]
        
        cols = int(query_params.get("cols", [str(len(types))])[0])
        rows = int(query_params.get("rows", ["100"])[0])
        lang = query_params.get("lang", ["es"])[0]
        
        results = self.ontology.recommend_by_data(types, cols, rows, lang=lang)
        
        return {
            "status": "ok",
            "input": {
                "column_types": types,
                "num_columns": cols,
                "num_rows": rows
            },
            "recommendations": [r.to_dict() for r in results]
        }
    
    def handle_get(self, chart_id: str, query_params: Dict[str, list]) -> Dict[str, Any]:
        """
        GET /api/charts/{chart_id}
        
        Returns:
            Todos los datos del gráfico o error 404
        """
        self._ensure_loaded()
        
        chart = self.ontology.get_chart(chart_id)
        
        if not chart:
            return {"status": "error", "message": f"Chart not found: {chart_id}"}
        
        # Serializar para JSON (convierte datetime a string)
        chart_serialized = _serialize_for_json(chart)
        
        return {
            "status": "ok",
            "chart": chart_serialized
        }
    
    def handle_code(self, chart_id: str, query_params: Dict[str, list]) -> Dict[str, Any]:
        """
        GET /api/charts/{chart_id}/code?language=python&library=matplotlib
        
        Query params:
            - language: python, r, julia, javascript (requerido)
            - library: matplotlib, ggplot2, etc. (requerido)
        
        Returns:
            {"status": "ok", "code": "...", "language": "...", "library": "..."}
        """
        self._ensure_loaded()
        
        language = query_params.get("language", [""])[0]
        library = query_params.get("library", [""])[0]
        
        if not language:
            return {"status": "error", "message": "Missing parameter 'language'"}
        if not library:
            return {"status": "error", "message": "Missing parameter 'library'"}
        
        code = self.ontology.get_implementation(chart_id, language, library)
        
        if code is None:
            # Verificar si el gráfico existe
            chart = self.ontology.get_chart(chart_id)
            if not chart:
                return {"status": "error", "message": f"Chart not found: {chart_id}"}
            
            # El gráfico existe pero no la implementación
            available = chart.get("implementations", {})
            return {
                "status": "error", 
                "message": f"Implementation not found: {language}/{library}",
                "available": available
            }
        
        return {
            "status": "ok",
            "chart_id": chart_id,
            "language": language,
            "library": library,
            "code": code
        }
    
    def handle_stats(self) -> Dict[str, Any]:
        """
        GET /api/charts/stats
        
        Returns:
            Estadísticas del catálogo de gráficos
        """
        self._ensure_loaded()
        
        stats = self.ontology.get_stats()
        
        return {
            "status": "ok",
            **stats
        }
    
    def route(self, path: str, query_params: Dict[str, list]) -> Dict[str, Any]:
        """
        Enruta una petición al handler apropiado.
        
        Args:
            path: Ruta sin el prefijo (ej: "search", "scatter-basic", "scatter-basic/code")
            query_params: Parámetros de query parseados
            
        Returns:
            Diccionario con la respuesta
        """
        # Normalizar path
        path = path.strip("/")
        
        # Rutas especiales
        if path == "" or path == "list":
            return self.handle_list(query_params)
        
        if path == "search":
            return self.handle_search(query_params)
        
        if path == "recommend":
            return self.handle_recommend(query_params)
        
        if path == "stats":
            return self.handle_stats()
        
        # Rutas con ID de gráfico
        parts = path.split("/")
        chart_id = parts[0]
        
        if len(parts) == 1:
            # GET /api/charts/{id}
            return self.handle_get(chart_id, query_params)
        
        if len(parts) == 2 and parts[1] == "code":
            # GET /api/charts/{id}/code
            return self.handle_code(chart_id, query_params)
        
        return {"status": "error", "message": f"Unknown route: {path}"}


# ============================================================================
# Función de integración para neven_http_server.py
# ============================================================================

# Singleton global para uso desde el servidor
_handlers: Optional[ChartHandlers] = None


def get_chart_handlers() -> ChartHandlers:
    """
    Obtiene la instancia singleton de ChartHandlers.
    """
    global _handlers
    if _handlers is None:
        _handlers = ChartHandlers()
    return _handlers


def handle_charts_request(path: str, query_string: str) -> tuple:
    """
    Función helper para integrar con NEVENHandler.
    
    Args:
        path: Ruta completa (ej: "api/charts/search")
        query_string: Query string sin el "?" (ej: "q=correlacion&lang=es")
        
    Returns:
        Tupla (json_response, status_code)
    
    Uso en neven_http_server.py:
        from scripts.ontology.chart_handlers import handle_charts_request
        
        if path.startswith('api/charts'):
            sub_path = path[11:]  # Remove 'api/charts/'
            response, status = handle_charts_request(sub_path, query_string)
            self._send_json(response, status)
            return
    """
    handlers = get_chart_handlers()
    
    # Parsear query params
    query_params = parse_qs(query_string) if query_string else {}
    
    # Extraer sub-ruta (remover "api/charts")
    if path.startswith("api/charts/"):
        sub_path = path[11:]
    elif path == "api/charts":
        sub_path = ""
    else:
        sub_path = path
    
    try:
        result = handlers.route(sub_path, query_params)
        status = 200 if result.get("status") == "ok" else 400
        return result, status
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500


# ============================================================================
# CLI para pruebas
# ============================================================================

if __name__ == "__main__":
    import sys
    
    # Simular requests
    test_requests = [
        ("api/charts/stats", ""),
        ("api/charts/search", "q=correlacion&lang=es"),
        ("api/charts/recommend", "types=numeric,numeric&cols=2&rows=100"),
        ("api/charts/scatter-basic", ""),
        ("api/charts/scatter-basic/code", "language=python&library=matplotlib"),
    ]
    
    print("Testing Chart Handlers\n" + "="*50)
    
    for path, query in test_requests:
        print(f"\n{path}?{query}" if query else f"\n{path}")
        print("-" * 40)
        
        response, status = handle_charts_request(path, query)
        
        if status == 200:
            # Resumir respuesta
            if "code" in response:
                response["code"] = f"[{len(response['code'])} chars]"
            if "chart" in response:
                response["chart"] = f"[chart data for {response['chart'].get('id', '?')}]"
        
        print(f"Status: {status}")
        print(json.dumps(response, indent=2, ensure_ascii=False)[:500])
