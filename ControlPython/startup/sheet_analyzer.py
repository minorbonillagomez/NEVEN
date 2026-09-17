# ═══════════════════════════════════════════════════════════════════════════════
# NEVEN v3.0 — Sheet Analyzer Module
# ═══════════════════════════════════════════════════════════════════════════════
# Analyzes Excel formulas to extract metadata for the AI agent.
# Part of the hybrid JS+Python architecture:
#   JS (Office.js) captures formulas → Python analyzes → AI interprets
#
# Functions:
#   extract_functions()    — Parse function names from formulas
#   normalize_patterns()   — Group similar formulas into patterns
#   build_dependency_graph() — Construct cell reference graph
#   identify_io_cells()    — Find input/output cells
#   calculate_complexity() — Compute formula complexity metrics
#   enrich_with_ontology() — Lookup functions in Excel ontology
#   analyze_sheet()        — Main entry point combining all analyses
#
# Author: NEVEN Team (Minor Bonilla Gómez)
# ═══════════════════════════════════════════════════════════════════════════════

import re
import os
import json
from collections import defaultdict
from typing import Dict, List, Tuple, Any, Optional

# ─── Language normalization ───────────────────────────────────────────────────
try:
    from excel_translations import normalize_formula, detect_language_from_formula
    _TRANSLATIONS_AVAILABLE = True
except ImportError:
    _TRANSLATIONS_AVAILABLE = False
    
    def normalize_formula(formula: str, language: str = "es") -> str:
        return formula
    
    def detect_language_from_formula(formula: str) -> Optional[str]:
        return None

# ─── Regex patterns for Excel formula parsing ─────────────────────────────────

# Matches Excel function names: =SUM(, =VLOOKUP(, =IF(, etc.
FUNCTION_PATTERN = re.compile(r'\b([A-Z][A-Z0-9_.]+)\s*\(', re.IGNORECASE)

# Matches cell references: A1, $A$1, Sheet1!A1, 'Sheet Name'!A1
CELL_REF_PATTERN = re.compile(
    r"(?:'[^']+?'!|[A-Za-z_][A-Za-z0-9_]*!)?" +  # Optional sheet reference
    r"\$?[A-Z]{1,3}\$?\d+",                       # Column + Row
    re.IGNORECASE
)

# Matches range references: A1:B10, $A$1:$B$10
RANGE_PATTERN = re.compile(
    r"(?:'[^']+?'!|[A-Za-z_][A-Za-z0-9_]*!)?" +
    r"\$?[A-Z]{1,3}\$?\d+:\$?[A-Z]{1,3}\$?\d+",
    re.IGNORECASE
)

# Named ranges and table references: Table1[Column], DataRange
NAMED_REF_PATTERN = re.compile(r'\b([A-Za-z_][A-Za-z0-9_]*)\s*(?:\[[^\]]+\])?', re.IGNORECASE)


# ─── Excel Ontology loader (graph.jsonl) ──────────────────────────────────────
# NOTE: This loads ONLY the Excel ontology (LIBROS EXCEL).
# The econometric ontology (LIBROS) is separate and used by other modules.

_excel_ontology_cache: Optional[Dict[str, Dict[str, Any]]] = None

# Paths to try for the EXCEL ontology specifically
_EXCEL_ONTOLOGY_PATHS = [
    # Production path
    r"C:\NEVEN\ontologia\LIBROS EXCEL\memory\ontology\graph.jsonl",
    # Development path (from NEVEN/ControlPython/startup/ → ONTOLOGIA/LIBROS EXCEL/)
    # __file__ is sheet_analyzer.py in startup/
    # Need: startup → ControlPython → NEVEN → NEVEN(root) → ONTOLOGIA
]

def _get_ontology_paths():
    """Get possible paths to the Excel ontology file."""
    paths = [r"C:\NEVEN\ontologia\LIBROS EXCEL\memory\ontology\graph.jsonl"]
    
    # Calculate development path relative to this file
    try:
        this_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up: startup → ControlPython → NEVEN → project root
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(this_dir)))
        dev_path = os.path.join(project_root, "ONTOLOGIA", "LIBROS EXCEL", 
                                "memory", "ontology", "graph.jsonl")
        paths.append(dev_path)
    except:
        pass
    
    return paths


def _load_excel_ontology() -> Dict[str, Dict[str, Any]]:
    """
    Load Excel ontology from graph.jsonl. Cached after first load.
    
    This loads ONLY the Excel functions ontology, not the econometric one.
    
    Returns:
        Dict mapping function names (uppercase) to their ontology data:
        {
            "VLOOKUP": {"category": "Lookup", "description": "...", ...},
            "IF": {"category": "Logical", "description": "...", ...},
        }
    """
    global _excel_ontology_cache
    if _excel_ontology_cache is not None:
        return _excel_ontology_cache
    
    _excel_ontology_cache = {}
    
    for path in _get_ontology_paths():
        if os.path.isfile(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            entry = json.loads(line)
                            # Only process ExcelFunction entities
                            if entry.get("op") == "create":
                                entity = entry.get("entity", {})
                                if entity.get("type") == "ExcelFunction":
                                    props = entity.get("properties", {})
                                    func_name = props.get("name", "").upper()
                                    if func_name:
                                        _excel_ontology_cache[func_name] = {
                                            "id": entity.get("id"),
                                            "category": props.get("category", ""),
                                            "description": props.get("description", ""),
                                            "syntax": props.get("syntax", ""),
                                            "best_practices": props.get("best_practices", []),
                                            "common_errors": props.get("common_errors", []),
                                        }
                                # Also extract patterns for reference
                                elif entity.get("type") == "Pattern":
                                    props = entity.get("properties", {})
                                    # Store patterns by functions_used
                                    for func in props.get("functions_used", []):
                                        func_upper = func.upper()
                                        if func_upper in _excel_ontology_cache:
                                            if "patterns" not in _excel_ontology_cache[func_upper]:
                                                _excel_ontology_cache[func_upper]["patterns"] = []
                                            _excel_ontology_cache[func_upper]["patterns"].append({
                                                "name": props.get("name"),
                                                "description": props.get("description"),
                                            })
                        except json.JSONDecodeError:
                            continue
                # Successfully loaded, break
                break
            except Exception:
                continue
    
    return _excel_ontology_cache


def _get_function_info(func_name: str) -> Optional[Dict[str, Any]]:
    """Lookup a function in the Excel ontology by name."""
    ontology = _load_excel_ontology()
    return ontology.get(func_name.upper())


# ─── Core analysis functions ──────────────────────────────────────────────────

def extract_functions(formulas: List[Dict[str, str]]) -> Dict[str, int]:
    """
    Extract unique Excel functions from a list of formulas.
    
    Args:
        formulas: List of {address: str, formula: str} dicts
    
    Returns:
        Dict mapping function names (uppercase) to occurrence counts
    
    Example:
        >>> extract_functions([{"address": "A1", "formula": "=SUM(B1:B10)"}])
        {"SUM": 1}
    """
    counts = defaultdict(int)
    
    for item in formulas:
        formula = item.get("formula", "")
        if not formula.startswith("="):
            continue
        
        # Find all function calls
        matches = FUNCTION_PATTERN.findall(formula)
        for func_name in matches:
            counts[func_name.upper()] += 1
    
    return dict(counts)


def normalize_patterns(formulas: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """
    Group formulas into patterns by replacing specific references with placeholders.
    
    This identifies formulas that are structurally identical but operate on
    different cells (e.g., =A1+B1 and =A2+B2 become the same pattern).
    
    Args:
        formulas: List of {address: str, formula: str} dicts
    
    Returns:
        List of patterns with counts and example addresses
    
    Example:
        >>> normalize_patterns([
        ...     {"address": "C1", "formula": "=A1+B1"},
        ...     {"address": "C2", "formula": "=A2+B2"}
        ... ])
        [{"pattern": "=<REF>+<REF>", "count": 2, "examples": ["C1", "C2"]}]
    """
    pattern_map = defaultdict(lambda: {"count": 0, "examples": []})
    
    for item in formulas:
        formula = item.get("formula", "")
        address = item.get("address", "")
        
        if not formula.startswith("="):
            continue
        
        # Normalize: replace cell refs with placeholders
        normalized = formula
        
        # Replace ranges first (before individual cells)
        normalized = RANGE_PATTERN.sub("<RANGE>", normalized)
        
        # Replace cell references
        normalized = CELL_REF_PATTERN.sub("<REF>", normalized)
        
        # Replace string literals
        normalized = re.sub(r'"[^"]*"', '<STR>', normalized)
        
        # Replace numbers (but keep function structure)
        normalized = re.sub(r'\b\d+\.?\d*\b', '<NUM>', normalized)
        
        pattern_map[normalized]["count"] += 1
        if len(pattern_map[normalized]["examples"]) < 5:  # Keep max 5 examples
            pattern_map[normalized]["examples"].append(address)
    
    # Convert to list and sort by count descending
    patterns = [
        {
            "pattern": pattern,
            "count": data["count"],
            "examples": data["examples"],
            "functions": list(set(FUNCTION_PATTERN.findall(pattern)))
        }
        for pattern, data in pattern_map.items()
    ]
    patterns.sort(key=lambda x: x["count"], reverse=True)
    
    return patterns


def build_dependency_graph(formulas: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Build a dependency graph showing which cells reference which.
    
    Args:
        formulas: List of {address: str, formula: str} dicts
    
    Returns:
        Dict with:
          - edges: List of {source, target} dependencies
          - nodes: Dict mapping addresses to their formula info
          - stats: Summary statistics
    """
    edges = []
    nodes = {}
    
    for item in formulas:
        address = item.get("address", "").upper()
        formula = item.get("formula", "")
        
        if not formula.startswith("="):
            continue
        
        # Extract all cell references
        refs = CELL_REF_PATTERN.findall(formula)
        
        # Also extract range references and expand to edges
        ranges = RANGE_PATTERN.findall(formula)
        
        nodes[address] = {
            "formula": formula,
            "ref_count": len(refs) + len(ranges),
            "functions": list(set(FUNCTION_PATTERN.findall(formula)))
        }
        
        # Create edges from referenced cells to this cell
        for ref in refs:
            ref_upper = ref.upper().replace("$", "")  # Normalize
            edges.append({"source": ref_upper, "target": address})
        
        # For ranges, create edge from range notation
        for rng in ranges:
            rng_upper = rng.upper().replace("$", "")
            edges.append({"source": rng_upper, "target": address, "is_range": True})
    
    # Calculate in-degree and out-degree
    in_degree = defaultdict(int)
    out_degree = defaultdict(int)
    for edge in edges:
        in_degree[edge["target"]] += 1
        out_degree[edge["source"]] += 1
    
    return {
        "edges": edges,
        "nodes": nodes,
        "stats": {
            "total_edges": len(edges),
            "total_nodes": len(nodes),
            "max_in_degree": max(in_degree.values()) if in_degree else 0,
            "max_out_degree": max(out_degree.values()) if out_degree else 0,
        }
    }


def identify_io_cells(formulas: List[Dict[str, str]], 
                      dependency_graph: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    """
    Identify input cells (no dependencies) and output cells (nothing depends on them).
    
    Args:
        formulas: Original formula list
        dependency_graph: Result from build_dependency_graph()
    
    Returns:
        Tuple of (input_cells, output_cells)
    """
    formula_cells = {item["address"].upper() for item in formulas 
                     if item.get("formula", "").startswith("=")}
    
    # Cells that are referenced by formulas
    referenced_cells = set()
    for edge in dependency_graph.get("edges", []):
        source = edge["source"]
        # Skip range references for input detection
        if not edge.get("is_range"):
            referenced_cells.add(source)
    
    # Cells that reference other cells (have formulas)
    referencing_cells = set()
    for edge in dependency_graph.get("edges", []):
        referencing_cells.add(edge["target"])
    
    # Inputs: Referenced but not containing formulas (pure inputs)
    inputs = list(referenced_cells - formula_cells)
    
    # Outputs: Formula cells that nothing else references
    targets = {edge["target"] for edge in dependency_graph.get("edges", [])}
    sources = {edge["source"] for edge in dependency_graph.get("edges", [])}
    outputs = list(formula_cells - sources)
    
    # Sort for consistent output
    inputs.sort()
    outputs.sort()
    
    return inputs[:50], outputs[:50]  # Limit to 50 each


def calculate_complexity(formulas: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Calculate complexity metrics for the sheet.
    
    Returns metrics like:
      - Average nesting depth
      - Most complex formulas
      - Function diversity index
    """
    if not formulas:
        return {"score": 0, "level": "empty", "details": {}}
    
    depths = []
    lengths = []
    all_functions = set()
    complex_formulas = []
    
    for item in formulas:
        formula = item.get("formula", "")
        if not formula.startswith("="):
            continue
        
        # Calculate nesting depth (count of parentheses depth)
        max_depth = 0
        current_depth = 0
        for char in formula:
            if char == '(':
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif char == ')':
                current_depth -= 1
        
        depths.append(max_depth)
        lengths.append(len(formula))
        
        # Collect functions
        funcs = FUNCTION_PATTERN.findall(formula)
        all_functions.update(f.upper() for f in funcs)
        
        # Track complex formulas
        if max_depth >= 3 or len(formula) > 100 or len(funcs) >= 3:
            complex_formulas.append({
                "address": item.get("address"),
                "depth": max_depth,
                "length": len(formula),
                "functions": len(funcs)
            })
    
    if not depths:
        return {"score": 0, "level": "empty", "details": {}}
    
    avg_depth = sum(depths) / len(depths)
    avg_length = sum(lengths) / len(lengths)
    func_diversity = len(all_functions)
    
    # Calculate complexity score (0-100)
    score = min(100, int(
        (avg_depth * 15) +           # Nesting contributes up to 45
        (avg_length / 10) +          # Length contributes up to 30
        (func_diversity * 2)         # Diversity contributes up to 25
    ))
    
    # Determine level
    if score < 20:
        level = "simple"
    elif score < 40:
        level = "moderate"
    elif score < 60:
        level = "complex"
    else:
        level = "advanced"
    
    # Sort complex formulas by a combined metric
    complex_formulas.sort(key=lambda x: x["depth"] * 10 + x["functions"], reverse=True)
    
    return {
        "score": score,
        "level": level,
        "details": {
            "avg_nesting_depth": round(avg_depth, 2),
            "avg_formula_length": round(avg_length, 1),
            "unique_functions": func_diversity,
            "total_formulas": len(depths),
            "max_nesting_depth": max(depths) if depths else 0,
        },
        "most_complex": complex_formulas[:10]  # Top 10 most complex
    }


def enrich_with_ontology(function_counts: Dict[str, int]) -> List[Dict[str, Any]]:
    """
    Enrich function counts with metadata from the Excel ontology.
    
    Uses the LIBROS EXCEL ontology (graph.jsonl) to add:
    - category, description, syntax
    - best_practices, common_errors
    - related patterns
    
    Args:
        function_counts: Dict from extract_functions()
    
    Returns:
        List of enriched function info with descriptions and categories
    """
    enriched = []
    
    for func_name, count in sorted(function_counts.items(), key=lambda x: -x[1]):
        info = _get_function_info(func_name)
        
        if info:
            entry = {
                "name": func_name,
                "count": count,
                "category": info.get("category", "Unknown"),
                "description": info.get("description", ""),
                "syntax": info.get("syntax", ""),
                "best_practices": info.get("best_practices", [])[:3],  # Limit to 3
                "common_errors": info.get("common_errors", [])[:3],    # Limit to 3
            }
            # Include patterns if available
            if info.get("patterns"):
                entry["patterns"] = [p.get("name") for p in info["patterns"][:2]]
            enriched.append(entry)
        else:
            # Function not in ontology (might be custom, newer, or misspelled)
            enriched.append({
                "name": func_name,
                "count": count,
                "category": _guess_category(func_name),
                "description": "",
                "syntax": "",
                "best_practices": [],
                "common_errors": [],
            })
    
    return enriched


def _guess_category(func_name: str) -> str:
    """Guess category for functions not in ontology based on name patterns."""
    fn = func_name.upper()
    
    # Common prefixes that indicate category
    if fn.startswith(("SUM", "COUNT", "AVERAGE", "MAX", "MIN", "LARGE", "SMALL")):
        return "Math & Stats"
    if fn.startswith(("VLOOKUP", "HLOOKUP", "XLOOKUP", "INDEX", "MATCH", "LOOKUP")):
        return "Lookup"
    if fn.startswith(("IF", "AND", "OR", "NOT", "XOR", "TRUE", "FALSE", "SWITCH")):
        return "Logical"
    if fn.startswith(("DATE", "TIME", "YEAR", "MONTH", "DAY", "HOUR", "MINUTE", "TODAY", "NOW")):
        return "Date and Time"
    if fn.startswith(("TEXT", "CONCAT", "LEFT", "RIGHT", "MID", "LEN", "TRIM", "UPPER", "LOWER")):
        return "Text"
    if fn.startswith(("PV", "FV", "PMT", "NPV", "IRR", "RATE", "XNPV", "XIRR")):
        return "Financial"
    
    return "Unknown"


def generate_mermaid_graph(dependency_graph: Dict[str, Any], max_edges: int = 50) -> str:
    """
    Generate a Mermaid flowchart from the dependency graph.
    
    Args:
        dependency_graph: Result from build_dependency_graph()
        max_edges: Maximum number of edges to include (for readability)
    
    Returns:
        Mermaid markdown string
    """
    edges = dependency_graph.get("edges", [])[:max_edges]
    
    if not edges:
        return "```mermaid\nflowchart LR\n    A[No dependencies found]\n```"
    
    lines = ["```mermaid", "flowchart LR"]
    
    # Add style classes
    lines.append("    classDef input fill:#90EE90,stroke:#228B22")
    lines.append("    classDef output fill:#FFB6C1,stroke:#DC143C")
    lines.append("    classDef formula fill:#87CEEB,stroke:#4682B4")
    
    # Track unique nodes for styling
    sources = set()
    targets = set()
    
    for edge in edges:
        source = edge["source"].replace(":", "_")  # Sanitize for Mermaid
        target = edge["target"].replace(":", "_")
        sources.add(source)
        targets.add(target)
        
        if edge.get("is_range"):
            lines.append(f"    {source}[/{edge['source']}/] --> {target}")
        else:
            lines.append(f"    {source} --> {target}")
    
    # Style inputs (sources that aren't targets)
    inputs = sources - targets
    outputs = targets - sources
    
    for inp in list(inputs)[:10]:
        lines.append(f"    class {inp} input")
    for out in list(outputs)[:10]:
        lines.append(f"    class {out} output")
    
    lines.append("```")
    
    return "\n".join(lines)


# ─── Main entry point ─────────────────────────────────────────────────────────

def analyze_sheet(body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entry point: Analyze a sheet's formulas and return structured metadata.
    
    Args:
        body: Request body with:
          - sheet_name: str — Name of the sheet
          - formulas: List[{address, formula}] — Formula cells from JS
          - total_cells: int — Total cell count in used range (optional)
          - include_graph: bool — Whether to include Mermaid graph (default: True)
          - language: str — Excel language code (auto-detected if not provided)
    
    Returns:
        Structured metadata for AI agent consumption
    """
    formulas = body.get("formulas", [])
    sheet_name = body.get("sheet_name", "Sheet1")
    total_cells = body.get("total_cells", 0)
    include_graph = body.get("include_graph", True)
    language = body.get("language", None)
    
    if not formulas:
        return {
            "status": "ok",
            "sheet_name": sheet_name,
            "summary": {
                "total_formulas": 0,
                "unique_patterns": 0,
                "functions_used": 0,
                "message": "No formulas found in the sheet"
            },
            "functions": [],
            "patterns": [],
            "dependencies": {"edges": [], "nodes": {}, "stats": {}},
            "critical_cells": {"inputs": [], "outputs": []},
            "complexity": {"score": 0, "level": "empty", "details": {}},
        }
    
    # Detect language if not provided
    detected_language = language
    if not detected_language and _TRANSLATIONS_AVAILABLE:
        # Sample first few formulas to detect language
        for item in formulas[:10]:
            detected = detect_language_from_formula(item.get("formula", ""))
            if detected:
                detected_language = detected
                break
    
    # Normalize formulas to English if needed
    normalized_formulas = formulas
    if detected_language and detected_language != "en" and _TRANSLATIONS_AVAILABLE:
        normalized_formulas = []
        for item in formulas:
            normalized_formulas.append({
                "address": item.get("address", ""),
                "formula": normalize_formula(item.get("formula", ""), detected_language),
                "original_formula": item.get("formula", "")  # Keep original for reference
            })
    
    # Run all analyses on normalized formulas
    function_counts = extract_functions(normalized_formulas)
    patterns = normalize_patterns(normalized_formulas)
    dependencies = build_dependency_graph(normalized_formulas)
    inputs, outputs = identify_io_cells(normalized_formulas, dependencies)
    complexity = calculate_complexity(normalized_formulas)
    enriched_functions = enrich_with_ontology(function_counts)
    
    result = {
        "status": "ok",
        "sheet_name": sheet_name,
        "detected_language": detected_language,
        "summary": {
            "total_formulas": len(formulas),
            "total_cells": total_cells,
            "formula_density": round(len(formulas) / max(total_cells, 1) * 100, 1),
            "unique_patterns": len(patterns),
            "functions_used": len(function_counts),
            "complexity_level": complexity.get("level", "unknown"),
        },
        "functions": enriched_functions,
        "patterns": patterns[:20],  # Top 20 patterns
        "dependencies": {
            "stats": dependencies.get("stats", {}),
            # Include edges only if not too many
            "edges": dependencies.get("edges", [])[:100] if len(dependencies.get("edges", [])) <= 100 else [],
            "edge_count": len(dependencies.get("edges", [])),
        },
        "critical_cells": {
            "inputs": inputs,
            "outputs": outputs,
        },
        "complexity": complexity,
    }
    
    # Optionally include Mermaid visualization
    if include_graph and dependencies.get("edges"):
        result["mermaid_graph"] = generate_mermaid_graph(dependencies)
    
    return result


# ─── Export for neven_http_server.py ──────────────────────────────────────────

__all__ = [
    "analyze_sheet",
    "extract_functions",
    "normalize_patterns",
    "build_dependency_graph",
    "identify_io_cells",
    "calculate_complexity",
    "enrich_with_ontology",
    "generate_mermaid_graph",
]
