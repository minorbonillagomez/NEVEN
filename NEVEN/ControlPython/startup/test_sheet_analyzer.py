# ═══════════════════════════════════════════════════════════════════════════════
# Tests for sheet_analyzer.py
# ═══════════════════════════════════════════════════════════════════════════════

import pytest
from sheet_analyzer import (
    extract_functions,
    normalize_patterns,
    build_dependency_graph,
    identify_io_cells,
    calculate_complexity,
    analyze_sheet,
    generate_mermaid_graph,
)


# ─── Test Data ────────────────────────────────────────────────────────────────

SAMPLE_FORMULAS = [
    {"address": "C1", "formula": "=A1+B1"},
    {"address": "C2", "formula": "=A2+B2"},
    {"address": "C3", "formula": "=A3+B3"},
    {"address": "D1", "formula": "=SUM(A1:A10)"},
    {"address": "D2", "formula": "=AVERAGE(B1:B10)"},
    {"address": "E1", "formula": "=IF(C1>0,\"Positive\",\"Negative\")"},
    {"address": "F1", "formula": "=VLOOKUP(A1,Sheet2!A:B,2,FALSE)"},
    {"address": "G1", "formula": "=INDEX(MATCH(A1,B:B,0),C:C)"},
]

COMPLEX_FORMULAS = [
    {"address": "A1", "formula": "=IF(AND(B1>0,C1<100),VLOOKUP(D1,Table1,2,FALSE),IFERROR(INDEX(MATCH(E1,F:F,0),G:G),0))"},
    {"address": "B1", "formula": "=SUMPRODUCT((A:A=\"X\")*(B:B>0))"},
    {"address": "C1", "formula": "=OFFSET(A1,MATCH(D1,E:E,0)-1,0,COUNTIF(F:F,G1),1)"},
]


# ─── Tests ────────────────────────────────────────────────────────────────────

class TestExtractFunctions:
    def test_basic_functions(self):
        result = extract_functions(SAMPLE_FORMULAS)
        assert "SUM" in result
        assert "AVERAGE" in result
        assert "IF" in result
        assert "VLOOKUP" in result
    
    def test_function_counts(self):
        # 3 formulas with just references, no functions
        simple = [{"address": "A1", "formula": "=B1+C1"}]
        result = extract_functions(simple)
        # No Excel functions, just operators
        assert len(result) == 0
    
    def test_nested_functions(self):
        result = extract_functions(COMPLEX_FORMULAS)
        # Should find IF, AND, VLOOKUP, IFERROR, INDEX, MATCH, etc.
        assert "IF" in result
        assert "VLOOKUP" in result
        assert "MATCH" in result
    
    def test_empty_input(self):
        result = extract_functions([])
        assert result == {}
    
    def test_non_formula_cells(self):
        cells = [{"address": "A1", "formula": "Hello"}, {"address": "A2", "formula": "123"}]
        result = extract_functions(cells)
        assert result == {}


class TestNormalizePatterns:
    def test_groups_similar_formulas(self):
        result = normalize_patterns(SAMPLE_FORMULAS)
        # =A1+B1, =A2+B2, =A3+B3 should become one pattern
        patterns = {p["pattern"] for p in result}
        assert "=<REF>+<REF>" in patterns
    
    def test_pattern_counts(self):
        result = normalize_patterns(SAMPLE_FORMULAS)
        # Find the =<REF>+<REF> pattern
        for p in result:
            if p["pattern"] == "=<REF>+<REF>":
                assert p["count"] == 3  # C1, C2, C3
                assert len(p["examples"]) == 3
                break
    
    def test_range_normalization(self):
        formulas = [{"address": "A1", "formula": "=SUM(B1:B100)"}]
        result = normalize_patterns(formulas)
        # Should normalize to =SUM(<RANGE>)
        assert any("<RANGE>" in p["pattern"] for p in result)
    
    def test_string_normalization(self):
        formulas = [{"address": "A1", "formula": "=IF(B1>0,\"Yes\",\"No\")"}]
        result = normalize_patterns(formulas)
        # Should normalize strings to <STR>
        assert any("<STR>" in p["pattern"] for p in result)


class TestBuildDependencyGraph:
    def test_creates_edges(self):
        formulas = [{"address": "C1", "formula": "=A1+B1"}]
        result = build_dependency_graph(formulas)
        edges = result["edges"]
        # C1 depends on A1 and B1
        sources = {e["source"] for e in edges}
        assert "A1" in sources
        assert "B1" in sources
    
    def test_tracks_nodes(self):
        result = build_dependency_graph(SAMPLE_FORMULAS)
        nodes = result["nodes"]
        assert "C1" in nodes
        assert "D1" in nodes
        assert nodes["C1"]["formula"] == "=A1+B1"
    
    def test_stats(self):
        result = build_dependency_graph(SAMPLE_FORMULAS)
        stats = result["stats"]
        assert "total_edges" in stats
        assert "total_nodes" in stats
        assert stats["total_nodes"] > 0


class TestIdentifyIOCells:
    def test_identifies_inputs(self):
        formulas = [
            {"address": "C1", "formula": "=A1+B1"},
            {"address": "C2", "formula": "=A2+B2"},
        ]
        graph = build_dependency_graph(formulas)
        inputs, outputs = identify_io_cells(formulas, graph)
        # A1, B1, A2, B2 are inputs (referenced but not formulas)
        assert "A1" in inputs or "B1" in inputs
    
    def test_identifies_outputs(self):
        formulas = [
            {"address": "B1", "formula": "=A1*2"},
            {"address": "C1", "formula": "=B1+10"},
        ]
        graph = build_dependency_graph(formulas)
        inputs, outputs = identify_io_cells(formulas, graph)
        # C1 is output (formula but nothing references it)
        assert "C1" in outputs


class TestCalculateComplexity:
    def test_simple_formulas(self):
        simple = [{"address": "A1", "formula": "=B1+C1"}]
        result = calculate_complexity(simple)
        assert result["level"] in ["simple", "moderate"]
        assert result["score"] < 30
    
    def test_complex_formulas(self):
        result = calculate_complexity(COMPLEX_FORMULAS)
        # These are deeply nested
        assert result["level"] in ["complex", "advanced"]
        assert result["details"]["max_nesting_depth"] >= 3
    
    def test_empty_input(self):
        result = calculate_complexity([])
        assert result["level"] == "empty"
        assert result["score"] == 0


class TestAnalyzeSheet:
    def test_full_analysis(self):
        body = {
            "sheet_name": "TestSheet",
            "formulas": SAMPLE_FORMULAS,
            "total_cells": 100,
        }
        result = analyze_sheet(body)
        
        assert result["status"] == "ok"
        assert result["sheet_name"] == "TestSheet"
        assert "summary" in result
        assert "functions" in result
        assert "patterns" in result
        assert "dependencies" in result
        assert "complexity" in result
    
    def test_empty_sheet(self):
        body = {"sheet_name": "Empty", "formulas": []}
        result = analyze_sheet(body)
        assert result["status"] == "ok"
        assert result["summary"]["total_formulas"] == 0
    
    def test_includes_mermaid_graph(self):
        body = {"formulas": SAMPLE_FORMULAS, "include_graph": True}
        result = analyze_sheet(body)
        if result.get("mermaid_graph"):
            assert "```mermaid" in result["mermaid_graph"]


class TestGenerateMermaidGraph:
    def test_generates_valid_mermaid(self):
        graph = build_dependency_graph(SAMPLE_FORMULAS)
        mermaid = generate_mermaid_graph(graph)
        assert "```mermaid" in mermaid
        assert "flowchart" in mermaid
    
    def test_empty_graph(self):
        mermaid = generate_mermaid_graph({"edges": [], "nodes": {}})
        assert "No dependencies found" in mermaid


# ─── Run tests ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
