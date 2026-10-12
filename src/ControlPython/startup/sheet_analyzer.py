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


# ─── Ontology Integration ─────────────────────────────────────────────────────
# Uses the multi-domain ontology_manager for Excel function lookups.
# Supports: excel, econometrics, and future domains.

try:
    from ontology_manager import get_manager, get_excel_function
    _ONTOLOGY_AVAILABLE = True
except ImportError:
    _ONTOLOGY_AVAILABLE = False
    
    def get_excel_function(name: str) -> Optional[Dict[str, Any]]:
        """Fallback when ontology_manager not available."""
        return None


def _get_function_info(func_name: str) -> Optional[Dict[str, Any]]:
    """
    Lookup a function in the Excel ontology by name.
    
    Uses the multi-domain ontology system via ontology_manager.
    Returns dict with category, description, syntax, best_practices, common_errors.
    """
    if not _ONTOLOGY_AVAILABLE:
        return None
    
    return get_excel_function(func_name)


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
    
    # Add style classes - fondo blanco, texto negro para visibilidad
    lines.append("    classDef input fill:#FFFFFF,stroke:#228B22,stroke-width:2px,color:#000000")
    lines.append("    classDef output fill:#FFFFFF,stroke:#DC143C,stroke-width:2px,color:#000000")
    lines.append("    classDef formula fill:#FFFFFF,stroke:#4682B4,stroke-width:2px,color:#000000")
    
    # Sanitize for Mermaid (no special chars, no leading digits)
    def _sanitize_node(name):
        safe = re.sub(r'[^A-Za-z0-9_]', '_', name)
        if safe and safe[0].isdigit():
            safe = 'N_' + safe
        return safe
    
    # Track unique nodes for styling
    sources = set()
    targets = set()
    
    for edge in edges:
        source_safe = _sanitize_node(edge["source"])
        target_safe = _sanitize_node(edge["target"])
        sources.add(source_safe)
        targets.add(target_safe)
        
        if edge.get("is_range"):
            lines.append(f"    {source_safe}[/{edge['source']}/] --> {target_safe}")
        else:
            lines.append(f"    {source_safe} --> {target_safe}")
    
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


# ═══════════════════════════════════════════════════════════════════════════════
# Workbook-level Analysis Functions
# ═══════════════════════════════════════════════════════════════════════════════
# Extends sheet analysis to full workbook scope:
#   - Cross-sheet references detection
#   - Workbook pattern classification
#   - Data flow graph between sheets
#   - Aggregated complexity metrics
# ═══════════════════════════════════════════════════════════════════════════════

# Pattern to detect cross-sheet references: Sheet1!A1, 'Sheet Name'!A1:B10
CROSS_SHEET_PATTERN = re.compile(
    r"(?:'([^']+)'!|([A-Za-z_][A-Za-z0-9_]*)!)"  # Sheet name (quoted or unquoted)
    r"\$?[A-Z]{1,3}\$?\d+",                       # Cell reference
    re.IGNORECASE
)

# External workbook reference: [Book.xlsx]Sheet!A1
EXTERNAL_REF_PATTERN = re.compile(
    r"\[([^\]]+)\]"                              # Workbook name in brackets
    r"(?:'([^']+)'!|([A-Za-z_][A-Za-z0-9_]*)!)"  # Sheet name
    r"\$?[A-Z]{1,3}\$?\d+",
    re.IGNORECASE
)


def extract_cross_sheet_references(sheets: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Detect formulas that reference other sheets within the workbook.
    
    Args:
        sheets: List of sheet data, each with {name, formulas: [{address, formula}]}
    
    Returns:
        {
            edges: [{from_sheet, to_sheet, formula_count, sample_formulas}],
            external_refs: [{book, sheet, count}],
            hub_sheets: [sheets with most incoming/outgoing refs],
            orphan_sheets: [sheets with no cross-references],
            stats: {total_cross_refs, sheets_with_refs, ...}
        }
    """
    # Build map of sheet names for quick lookup
    sheet_names = {s.get("name", "").lower(): s.get("name", "") for s in sheets}
    
    # Count references: (from_sheet, to_sheet) -> [formulas]
    cross_refs = defaultdict(list)
    external_refs = defaultdict(int)
    
    # DEBUG counters
    debug_total_formulas = 0
    debug_formulas_with_bang = 0
    debug_matches_found = 0
    debug_sample_no_match = []
    
    for sheet in sheets:
        from_sheet = sheet.get("name", "Unknown")
        formulas = sheet.get("formulas", [])
        
        # DEBUG: Log formulas count per sheet
        print(f"[DEBUG cross_refs] Sheet '{from_sheet}': {len(formulas)} formulas")
        debug_total_formulas += len(formulas)
        
        for item in formulas:
            formula = item.get("formula", "")
            address = item.get("address", "")
            
            if not formula.startswith("="):
                continue
            
            # Check for external references first
            ext_matches = EXTERNAL_REF_PATTERN.findall(formula)
            for book, quoted_sheet, unquoted_sheet in ext_matches:
                ref_sheet = quoted_sheet or unquoted_sheet
                external_refs[(book, ref_sheet)] += 1
            
            # Check for cross-sheet references within workbook
            matches = CROSS_SHEET_PATTERN.findall(formula)
            
            # DEBUG: Track formulas with '!'
            if '!' in formula:
                debug_formulas_with_bang += 1
                if not matches and len(debug_sample_no_match) < 5:
                    debug_sample_no_match.append(formula[:100])
                    print(f"[DEBUG cross_refs] NO MATCH for formula with '!': {formula[:80]}")
                elif matches:
                    debug_matches_found += 1
                    print(f"[DEBUG cross_refs] MATCH in '{from_sheet}': {matches} <- {formula[:60]}")
            
            for quoted_name, unquoted_name in matches:
                to_sheet_raw = quoted_name or unquoted_name
                to_sheet_lower = to_sheet_raw.lower()
                
                # Skip self-references
                if to_sheet_lower == from_sheet.lower():
                    continue
                
                # Resolve to actual sheet name if it exists
                to_sheet = sheet_names.get(to_sheet_lower, to_sheet_raw)
                
                key = (from_sheet, to_sheet)
                if len(cross_refs[key]) < 5:  # Keep max 5 sample formulas
                    cross_refs[key].append({
                        "address": address,
                        "formula": formula[:100]  # Truncate long formulas
                    })
                else:
                    # Just increment count without adding more samples
                    cross_refs[key].append(None)
    
    # Convert to edges list
    edges = []
    for (from_sheet, to_sheet), samples in cross_refs.items():
        valid_samples = [s for s in samples if s is not None]
        edges.append({
            "from_sheet": from_sheet,
            "to_sheet": to_sheet,
            "formula_count": len(samples),
            "sample_formulas": valid_samples[:3]
        })
    
    # Sort by formula count descending
    edges.sort(key=lambda x: x["formula_count"], reverse=True)
    
    # Convert external refs
    ext_refs_list = [
        {"book": book, "sheet": sheet, "count": count}
        for (book, sheet), count in external_refs.items()
    ]
    ext_refs_list.sort(key=lambda x: x["count"], reverse=True)
    
    # Calculate in-degree and out-degree per sheet
    in_degree = defaultdict(int)
    out_degree = defaultdict(int)
    for edge in edges:
        out_degree[edge["from_sheet"]] += edge["formula_count"]
        in_degree[edge["to_sheet"]] += edge["formula_count"]
    
    # Find hub sheets (high connectivity)
    all_sheets = {s.get("name", "") for s in sheets}
    connected_sheets = set(in_degree.keys()) | set(out_degree.keys())
    orphan_sheets = list(all_sheets - connected_sheets)
    
    # Hub sheets: top 3 by total degree
    total_degree = {s: in_degree[s] + out_degree[s] for s in connected_sheets}
    hub_sheets = sorted(total_degree.items(), key=lambda x: -x[1])[:3]
    hub_sheets = [{"sheet": s, "total_refs": d, "in": in_degree[s], "out": out_degree[s]} 
                  for s, d in hub_sheets]
    
    return {
        "edges": edges,
        "external_refs": ext_refs_list,
        "hub_sheets": hub_sheets,
        "orphan_sheets": orphan_sheets,
        "stats": {
            "total_cross_refs": sum(e["formula_count"] for e in edges),
            "total_external_refs": sum(e["count"] for e in ext_refs_list),
            "sheets_with_outgoing": len(set(e["from_sheet"] for e in edges)),
            "sheets_with_incoming": len(set(e["to_sheet"] for e in edges)),
            "orphan_count": len(orphan_sheets),
        },
        # DEBUG info - remove after fixing
        "_debug": {
            "total_formulas_received": debug_total_formulas,
            "formulas_with_bang": debug_formulas_with_bang,
            "matches_found": debug_matches_found,
            "sample_no_match": debug_sample_no_match
        }
    }


def detect_workbook_pattern(sheets: List[Dict], cross_refs: Dict) -> Dict[str, Any]:
    """
    Classify workbook into common architectural patterns.
    
    Patterns detected:
      - financial_model: Input sheet(s) → Calculation sheet(s) → Summary/Output
      - dashboard: One main sheet with charts/summaries referencing data sheets
      - database: Large data sheet + query/pivot sheets
      - single_sheet: All work in one sheet (no cross-refs)
      - hub_and_spoke: One central sheet with many connections
      - chain: Linear flow Sheet1 → Sheet2 → Sheet3
      - mesh: Many interconnections between sheets
    
    Args:
        sheets: List of sheet data with analysis results
        cross_refs: Result from extract_cross_sheet_references()
    
    Returns:
        {
            pattern: str,
            confidence: float (0-1),
            characteristics: [str],
            suggestions: [str]
        }
    """
    edges = cross_refs.get("edges", [])
    stats = cross_refs.get("stats", {})
    orphans = cross_refs.get("orphan_sheets", [])
    hubs = cross_refs.get("hub_sheets", [])
    
    num_sheets = len(sheets)
    num_edges = len(edges)
    total_refs = stats.get("total_cross_refs", 0)
    
    # Special case: single sheet or no cross-references
    if num_sheets == 1:
        return {
            "pattern": "single_sheet",
            "confidence": 1.0,
            "characteristics": ["All work contained in one sheet"],
            "suggestions": ["Consider splitting into multiple sheets if complexity grows"]
        }
    
    if num_edges == 0:
        return {
            "pattern": "isolated_sheets",
            "confidence": 1.0,
            "characteristics": [
                f"{num_sheets} sheets with no cross-references",
                "Sheets operate independently"
            ],
            "suggestions": [
                "Consider if sheets should be in separate workbooks",
                "Or add references to create a cohesive model"
            ]
        }
    
    # Analyze graph structure
    # Build adjacency for analysis
    from_sheets = set(e["from_sheet"] for e in edges)
    to_sheets = set(e["to_sheet"] for e in edges)
    
    # Sheets that only receive (potential outputs/summaries)
    only_receivers = to_sheets - from_sheets
    # Sheets that only send (potential inputs/data)
    only_senders = from_sheets - to_sheets
    # Sheets that both send and receive (processing)
    bidirectional = from_sheets & to_sheets
    
    characteristics = []
    suggestions = []
    
    # Pattern: Hub and Spoke
    if hubs and hubs[0]["total_refs"] > total_refs * 0.5:
        hub_name = hubs[0]["sheet"]
        return {
            "pattern": "hub_and_spoke",
            "confidence": 0.85,
            "characteristics": [
                f"Central hub: '{hub_name}' with {hubs[0]['total_refs']} references",
                f"{hubs[0]['in']} incoming, {hubs[0]['out']} outgoing",
                f"{len(orphans)} disconnected sheets" if orphans else "All sheets connected"
            ],
            "suggestions": [
                f"'{hub_name}' is critical - changes may affect many sheets",
                "Consider documenting the hub sheet structure",
                "Review if hub is becoming too complex"
            ]
        }
    
    # Pattern: Financial Model (inputs → calcs → summary)
    if only_senders and only_receivers and bidirectional:
        # Check for typical naming patterns
        input_names = [s.lower() for s in only_senders]
        output_names = [s.lower() for s in only_receivers]
        
        has_input_sheet = any(n in s for s in input_names for n in ['input', 'data', 'param', 'assum'])
        has_output_sheet = any(n in s for s in output_names for n in ['summary', 'output', 'result', 'report', 'dashboard'])
        
        if has_input_sheet or has_output_sheet or len(bidirectional) >= 1:
            return {
                "pattern": "financial_model",
                "confidence": 0.80 if (has_input_sheet and has_output_sheet) else 0.65,
                "characteristics": [
                    f"Input sheets ({len(only_senders)}): {', '.join(list(only_senders)[:3])}",
                    f"Processing sheets ({len(bidirectional)}): {', '.join(list(bidirectional)[:3])}" if bidirectional else None,
                    f"Output sheets ({len(only_receivers)}): {', '.join(list(only_receivers)[:3])}"
                ],
                "suggestions": [
                    "Validate input sheets have data validation",
                    "Consider naming convention: Inputs_, Calc_, Output_",
                    "Document assumptions in input sheets"
                ]
            }
    
    # Pattern: Chain (linear flow)
    if len(edges) == num_sheets - 1 and len(only_senders) == 1 and len(only_receivers) == 1:
        return {
            "pattern": "chain",
            "confidence": 0.75,
            "characteristics": [
                "Linear data flow between sheets",
                f"Start: {list(only_senders)[0]}",
                f"End: {list(only_receivers)[0]}"
            ],
            "suggestions": [
                "Good for step-by-step processes",
                "Consider adding error checking between steps"
            ]
        }
    
    # Pattern: Dashboard
    if len(only_receivers) == 1 and len(only_senders) >= 2:
        dashboard_sheet = list(only_receivers)[0]
        return {
            "pattern": "dashboard",
            "confidence": 0.70,
            "characteristics": [
                f"Dashboard sheet: '{dashboard_sheet}'",
                f"Data sources: {len(only_senders)} sheets",
                f"Sources: {', '.join(list(only_senders)[:4])}"
            ],
            "suggestions": [
                "Ensure data sheets have consistent structure",
                "Consider using named ranges for dashboard references",
                "Add refresh timestamp to dashboard"
            ]
        }
    
    # Pattern: Database style
    # Look for one large sheet (many rows) referenced by others
    sheet_sizes = {s.get("name"): s.get("total_cells", 0) for s in sheets}
    max_size_sheet = max(sheet_sizes.items(), key=lambda x: x[1]) if sheet_sizes else (None, 0)
    
    if max_size_sheet[1] > 1000 and max_size_sheet[0] in only_senders:
        return {
            "pattern": "database",
            "confidence": 0.65,
            "characteristics": [
                f"Data sheet: '{max_size_sheet[0]}' ({max_size_sheet[1]} cells)",
                f"Query sheets: {len(only_receivers)}",
                "Large dataset with lookup/query pattern"
            ],
            "suggestions": [
                "Consider using Tables for the data sheet",
                "Use structured references (Table[Column])",
                "May benefit from Power Query for complex queries"
            ]
        }
    
    # Pattern: Mesh (many interconnections)
    connectivity = num_edges / max(num_sheets * (num_sheets - 1), 1)
    if connectivity > 0.3:
        return {
            "pattern": "mesh",
            "confidence": 0.60,
            "characteristics": [
                f"High connectivity: {connectivity:.0%} of possible connections",
                f"{num_edges} cross-sheet reference groups",
                "Complex interdependencies between sheets"
            ],
            "suggestions": [
                "Document the relationships between sheets",
                "Consider if some connections can be simplified",
                "Be careful with circular dependencies"
            ]
        }
    
    # Default: mixed/unclear pattern
    return {
        "pattern": "mixed",
        "confidence": 0.50,
        "characteristics": [
            f"{num_sheets} sheets with {num_edges} cross-reference groups",
            f"Orphan sheets: {len(orphans)}" if orphans else "All sheets connected",
            f"Total cross-references: {total_refs}"
        ],
        "suggestions": [
            "Consider organizing sheets into clear categories",
            "Review if all cross-references are necessary"
        ]
    }


def build_workbook_data_flow(sheets: List[Dict], cross_refs: Dict) -> Dict[str, Any]:
    """
    Build a directed graph showing data flow between sheets.
    
    Classifies each sheet as:
      - input: Only sends data (no incoming refs from other sheets)
      - output: Only receives data (no outgoing refs to other sheets)
      - processing: Both sends and receives
      - isolated: No cross-sheet references
    
    Args:
        sheets: List of sheet data
        cross_refs: Result from extract_cross_sheet_references()
    
    Returns:
        {
            nodes: [{name, role, formula_count, complexity_score}],
            edges: [{source, target, weight}],
            critical_path: [sheet_name, ...],
            mermaid: str
        }
    """
    edges_data = cross_refs.get("edges", [])
    
    # Build adjacency info
    from_sheets = defaultdict(int)  # sheet -> outgoing count
    to_sheets = defaultdict(int)    # sheet -> incoming count
    
    for edge in edges_data:
        from_sheets[edge["from_sheet"]] += edge["formula_count"]
        to_sheets[edge["to_sheet"]] += edge["formula_count"]
    
    all_sheet_names = {s.get("name", "") for s in sheets}
    connected = set(from_sheets.keys()) | set(to_sheets.keys())
    
    # Classify nodes
    nodes = []
    for sheet in sheets:
        name = sheet.get("name", "")
        has_outgoing = name in from_sheets
        has_incoming = name in to_sheets
        
        if has_outgoing and has_incoming:
            role = "processing"
        elif has_outgoing:
            role = "input"
        elif has_incoming:
            role = "output"
        else:
            role = "isolated"
        
        # Get complexity from sheet analysis if available
        complexity = sheet.get("complexity", {})
        
        nodes.append({
            "name": name,
            "role": role,
            "formula_count": len(sheet.get("formulas", [])),
            "complexity_score": complexity.get("score", 0),
            "complexity_level": complexity.get("level", "unknown"),
            "outgoing_refs": from_sheets.get(name, 0),
            "incoming_refs": to_sheets.get(name, 0)
        })
    
    # Build edges for visualization
    flow_edges = []
    for edge in edges_data:
        flow_edges.append({
            "source": edge["from_sheet"],
            "target": edge["to_sheet"],
            "weight": edge["formula_count"]
        })
    
    # Find critical path (longest dependency chain)
    # Simple BFS from input nodes
    critical_path = _find_longest_path(nodes, flow_edges)
    
    # Generate Mermaid diagram
    mermaid = _generate_workbook_mermaid(nodes, flow_edges)
    
    return {
        "nodes": nodes,
        "edges": flow_edges,
        "critical_path": critical_path,
        "mermaid": mermaid
    }


def _find_longest_path(nodes: List[Dict], edges: List[Dict]) -> List[str]:
    """Find the longest dependency path in the workbook."""
    if not edges:
        return []
    
    # Build adjacency list
    adj = defaultdict(list)
    for edge in edges:
        adj[edge["source"]].append(edge["target"])
    
    # Find input nodes (no incoming edges)
    all_targets = {e["target"] for e in edges}
    all_sources = {e["source"] for e in edges}
    start_nodes = all_sources - all_targets
    
    if not start_nodes:
        # Cycle or no clear start - just pick first source
        start_nodes = {edges[0]["source"]} if edges else set()
    
    # BFS/DFS to find longest path
    longest = []
    
    def dfs(node, path, visited):
        nonlocal longest
        if len(path) > len(longest):
            longest = path.copy()
        
        for next_node in adj.get(node, []):
            if next_node not in visited:
                visited.add(next_node)
                path.append(next_node)
                dfs(next_node, path, visited)
                path.pop()
                visited.remove(next_node)
    
    for start in start_nodes:
        dfs(start, [start], {start})
    
    return longest


def _generate_workbook_mermaid(nodes: List[Dict], edges: List[Dict]) -> str:
    """Generate Mermaid flowchart for workbook data flow."""
    if not nodes:
        return "```mermaid\nflowchart LR\n    A[No sheets]\n```"
    
    lines = ["```mermaid", "flowchart LR"]
    
    # Style classes for roles - fondo blanco, texto negro para visibilidad
    lines.append("    classDef input fill:#FFFFFF,stroke:#228B22,stroke-width:2px,color:#000000")
    lines.append("    classDef output fill:#FFFFFF,stroke:#DC143C,stroke-width:2px,color:#000000")
    lines.append("    classDef processing fill:#FFFFFF,stroke:#4682B4,stroke-width:2px,color:#000000")
    lines.append("    classDef isolated fill:#FFFFFF,stroke:#808080,stroke-width:1px,stroke-dasharray:5,color:#000000")
    
    # Sanitize names for Mermaid (remove spaces, special chars)
    # Node IDs cannot start with a number in Mermaid
    def sanitize(name):
        safe = re.sub(r'[^A-Za-z0-9_]', '_', name)
        # Prefix with 'S_' if starts with digit (Mermaid requirement)
        if safe and safe[0].isdigit():
            safe = 'S_' + safe
        return safe
    
    # Add nodes with labels
    for node in nodes:
        name = node["name"]
        safe_name = sanitize(name)
        role = node["role"]
        # Escapar comillas en la etiqueta visible
        label = name.replace('"', "'").replace('<', '').replace('>', '')
        
        # Node shape based on role (sin formas especiales que causen problemas)
        if role == "input":
            lines.append(f'    {safe_name}["{label}"]')
        elif role == "output":
            lines.append(f'    {safe_name}["{label}"]')
        elif role == "processing":
            lines.append(f'    {safe_name}["{label}"]')
        else:  # isolated
            lines.append(f'    {safe_name}["{label}"]')
        
        # Apply class
        lines.append(f"    class {safe_name} {role}")
    
    # Add edges (limit to avoid huge diagrams)
    max_edges = 50
    for edge in edges[:max_edges]:
        src = sanitize(edge["source"])
        tgt = sanitize(edge["target"])
        weight = edge["weight"]
        
        if weight > 10:
            lines.append(f"    {src} ==>|{weight}| {tgt}")  # Thick line
        elif weight > 1:
            lines.append(f"    {src} -->|{weight}| {tgt}")
        else:
            lines.append(f"    {src} --> {tgt}")
    
    if len(edges) > max_edges:
        lines.append(f"    %% {len(edges) - max_edges} conexiones adicionales omitidas")
    
    lines.append("```")
    return "\n".join(lines)


def analyze_workbook(body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entry point: Analyze entire workbook with all sheets.
    
    Args:
        body: {
            workbook_name: str,
            sheets: [{name, formulas, cell_values, total_cells}, ...],
            include_graph: bool (default True)
        }
    
    Returns:
        {
            status: "ok",
            workbook_name: str,
            sheet_count: int,
            captured_sheets: int,
            sheets: [analyze_sheet() result for each],
            cross_sheet_dependencies: {...},
            workbook_pattern: {...},
            data_flow: {...},
            aggregated_stats: {...},
            recommendations: [...]
        }
    """
    workbook_name = body.get("workbook_name", "Workbook")
    sheets_data = body.get("sheets", [])
    include_graph = body.get("include_graph", True)
    total_sheets = body.get("total_sheets", len(sheets_data))
    
    if not sheets_data:
        return {
            "status": "ok",
            "workbook_name": workbook_name,
            "sheet_count": 0,
            "message": "No sheets provided for analysis"
        }
    
    # Analyze each sheet individually
    sheet_analyses = []
    total_formulas = 0
    total_functions = set()
    max_complexity = 0
    
    for sheet in sheets_data:
        # Call existing analyze_sheet for each
        analysis = analyze_sheet({
            "sheet_name": sheet.get("name", "Sheet"),
            "formulas": sheet.get("formulas", []),
            "cell_values": sheet.get("cell_values", {}),
            "total_cells": sheet.get("total_cells", 0),
            "include_graph": False  # Don't include per-sheet graphs
        })
        
        # Add sheet-level data for cross-sheet analysis
        analysis["_formulas"] = sheet.get("formulas", [])
        
        sheet_analyses.append(analysis)
        
        # Aggregate stats
        total_formulas += analysis.get("summary", {}).get("total_formulas", 0)
        for func in analysis.get("functions", []):
            total_functions.add(func.get("name", ""))
        complexity_score = analysis.get("complexity", {}).get("score", 0)
        if complexity_score > max_complexity:
            max_complexity = complexity_score
    
    # Prepare sheets for cross-reference analysis (need name + formulas)
    sheets_for_cross_ref = [
        {
            "name": sheet_analyses[i].get("sheet_name", f"Sheet{i+1}"),
            "formulas": sheets_data[i].get("formulas", []),
            "total_cells": sheets_data[i].get("total_cells", 0),
            "complexity": sheet_analyses[i].get("complexity", {})
        }
        for i in range(len(sheets_data))
    ]
    
    # Cross-sheet analysis
    cross_refs = extract_cross_sheet_references(sheets_for_cross_ref)
    
    # Pattern detection
    pattern = detect_workbook_pattern(sheets_for_cross_ref, cross_refs)
    
    # Data flow graph
    data_flow = build_workbook_data_flow(sheets_for_cross_ref, cross_refs)
    
    # Clean up internal fields from sheet analyses
    for analysis in sheet_analyses:
        analysis.pop("_formulas", None)
    
    # Build recommendations
    recommendations = _generate_workbook_recommendations(
        sheet_analyses, cross_refs, pattern, data_flow
    )
    
    # Aggregated statistics
    aggregated = {
        "total_sheets": total_sheets,
        "analyzed_sheets": len(sheets_data),
        "total_formulas": total_formulas,
        "unique_functions": len(total_functions),
        "max_complexity_score": max_complexity,
        "cross_sheet_references": cross_refs.get("stats", {}).get("total_cross_refs", 0),
        "external_references": cross_refs.get("stats", {}).get("total_external_refs", 0),
        "orphan_sheets": len(cross_refs.get("orphan_sheets", [])),
    }
    
    result = {
        "status": "ok",
        "workbook_name": workbook_name,
        "sheet_count": total_sheets,
        "captured_sheets": len(sheets_data),
        "sheets": sheet_analyses,
        "cross_sheet_dependencies": {
            "edges": cross_refs.get("edges", [])[:20],  # Limit for readability
            "hub_sheets": cross_refs.get("hub_sheets", []),
            "orphan_sheets": cross_refs.get("orphan_sheets", []),
            "external_refs": cross_refs.get("external_refs", [])[:10],
            "stats": cross_refs.get("stats", {})
        },
        "workbook_pattern": pattern,
        "data_flow": {
            "nodes": data_flow.get("nodes", []),
            "edges": data_flow.get("edges", []),  # FIX: Include edges for D3 graph
            "critical_path": data_flow.get("critical_path", []),
        },
        "aggregated_stats": aggregated,
        "recommendations": recommendations
    }
    
    # Include Mermaid graph if requested
    if include_graph and data_flow.get("mermaid"):
        result["data_flow"]["mermaid"] = data_flow["mermaid"]
    
    return result


def _generate_workbook_recommendations(
    sheet_analyses: List[Dict],
    cross_refs: Dict,
    pattern: Dict,
    data_flow: Dict
) -> List[Dict[str, str]]:
    """Generate actionable recommendations based on workbook analysis."""
    recommendations = []
    
    # From pattern analysis
    for suggestion in pattern.get("suggestions", []):
        recommendations.append({
            "type": "pattern",
            "priority": "medium",
            "message": suggestion
        })
    
    # Check for high complexity sheets
    for analysis in sheet_analyses:
        complexity = analysis.get("complexity", {})
        if complexity.get("score", 0) >= 60:
            sheet_name = analysis.get("sheet_name", "Sheet")
            recommendations.append({
                "type": "complexity",
                "priority": "high",
                "message": f"Sheet '{sheet_name}' has high complexity (score: {complexity['score']}). Consider breaking into smaller sheets."
            })
    
    # Check for orphan sheets
    orphans = cross_refs.get("orphan_sheets", [])
    if orphans:
        recommendations.append({
            "type": "structure",
            "priority": "low",
            "message": f"Sheets with no cross-references: {', '.join(orphans[:5])}. Verify if they should be connected or removed."
        })
    
    # Check for external references
    ext_refs = cross_refs.get("external_refs", [])
    if ext_refs:
        recommendations.append({
            "type": "dependency",
            "priority": "medium",
            "message": f"External workbook references found ({len(ext_refs)} sources). Ensure linked workbooks are available."
        })
    
    # Check for long critical path
    critical_path = data_flow.get("critical_path", [])
    if len(critical_path) >= 4:
        recommendations.append({
            "type": "structure",
            "priority": "medium",
            "message": f"Long dependency chain ({len(critical_path)} sheets): {' → '.join(critical_path)}. Changes early in chain may cascade."
        })
    
    # Check for sheets with no formulas
    empty_sheets = [a.get("sheet_name") for a in sheet_analyses 
                    if a.get("summary", {}).get("total_formulas", 0) == 0]
    if empty_sheets and len(empty_sheets) < len(sheet_analyses):
        recommendations.append({
            "type": "content",
            "priority": "low",
            "message": f"Sheets without formulas: {', '.join(empty_sheets[:5])}. These may be data-only sheets."
        })
    
    # Sort by priority
    priority_order = {"high": 0, "medium": 1, "low": 2}
    recommendations.sort(key=lambda x: priority_order.get(x.get("priority", "low"), 2))
    
    return recommendations[:10]  # Limit to top 10


# ─── Export for neven_http_server.py ──────────────────────────────────────────

__all__ = [
    # Sheet-level analysis
    "analyze_sheet",
    "extract_functions",
    "normalize_patterns",
    "build_dependency_graph",
    "identify_io_cells",
    "calculate_complexity",
    "enrich_with_ontology",
    "generate_mermaid_graph",
    # Workbook-level analysis
    "analyze_workbook",
    "extract_cross_sheet_references",
    "detect_workbook_pattern",
    "build_workbook_data_flow",
]
