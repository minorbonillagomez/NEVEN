---
name: ontology-book-processor
description: Process PDF books to extract structured knowledge and add it to domain-specific ontologies. Use when the user says "procesa el libro", "agregar libro a la ontología", "incorporar PDF", "expandir ontología con libro", or mentions adding content from books like CFI Excel, Curso Práctico, Excel Bible, Wooldridge, Greene, or Hamilton to the NEVEN knowledge graph.
---

# Skill: Ontology Book Processor

## Purpose

Process PDF books to extract structured knowledge and add it to domain-specific ontologies in the NEVEN project. This skill transforms unstructured book content into graph-based knowledge (entities + relations) following a consistent schema.

## When to Use

Activate this skill when:
- User says "Procesa el libro [X] para la ontología [Y]"
- User adds a new PDF to `ONTOLOGIA/LIBROS*/` and wants to incorporate it
- User asks to expand an ontology with content from a book
- User mentions "agregar libro", "incorporar PDF", "expandir ontología"

## Ontology Domains

| Domain | Folder | Schema |
|--------|--------|--------|
| Econometrics | `ONTOLOGIA/LIBROS/` | `memory/ontology/schema.yaml` |
| Excel/Financial Modeling | `ONTOLOGIA/LIBROS EXCEL/` | `memory/ontology/schema.yaml` |
| Statistics | `ONTOLOGIA/LIBROS ESTADISTICA/` | (future) |

## Process Overview

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│  PDF Book   │ ──► │  Extract &   │ ──► │  Structure  │ ──► │  Validate &  │
│  (source)   │     │  Analyze     │     │  as JSONL   │     │  Append      │
└─────────────┘     └──────────────┘     └─────────────┘     └──────────────┘
```

## Step-by-Step Instructions

### Step 1: Identify Domain and Schema

1. Determine which ontology domain the book belongs to
2. Read the corresponding `schema.yaml` to understand valid entity types and relations
3. Note the existing `graph.jsonl` to understand current coverage

### Step 2: Extract Book Content

1. Read the PDF and identify its structure (chapters, sections)
2. Extract key concepts organized by chapter:
   - **Techniques** — Methods or procedures described
   - **Patterns** — Common formula patterns or model structures
   - **Best Practices** — Professional recommendations
   - **Common Errors** — Mistakes to avoid
   - **Concepts** — Definitions and theory
   - **Functions** — Excel/R functions mentioned with context

### Step 3: Structure as Entities

For each extracted concept, create an entity following the schema:

```json
{
  "op": "create",
  "entity": {
    "id": "technique_data_validation",
    "type": "Technique",
    "properties": {
      "name": "Data Validation for Input Cells",
      "description": "Using Excel's Data Validation to restrict input values...",
      "steps": ["Select input cells", "Data > Data Validation", "..."],
      "reference": {
        "book": "CFI Excel eBook",
        "chapter": "Chapter 3: Best Practices",
        "pages": "pp. 45-48"
      }
    }
  }
}
```

### Step 4: Create Relations

Connect entities using valid relations from the schema:

```json
{"op": "relate", "from": "technique_data_validation", "rel": "part_of", "to": "domain_financial_modeling"}
{"op": "relate", "from": "technique_data_validation", "rel": "prevents", "to": "error_invalid_inputs"}
{"op": "relate", "from": "best_practice_color_coding", "rel": "improves", "to": "technique_data_validation"}
```

### Step 5: Validate

1. Check all entity types exist in schema
2. Verify all relations use valid from/to types
3. Ensure no isolated nodes (every entity has at least one relation)
4. Check for duplicate IDs

### Step 6: Append to Graph

1. Read existing `graph.jsonl`
2. Append new entities and relations
3. Write updated file
4. Report statistics: entities added, relations added, coverage

## Entity ID Conventions

Use lowercase with underscores, prefixed by type:

| Type | Prefix | Example |
|------|--------|---------|
| Domain | `domain_` | `domain_financial_modeling` |
| Technique | `technique_` | `technique_goal_seek` |
| Pattern | `pattern_` | `pattern_circular_reference` |
| BestPractice | `bp_` | `bp_color_coding` |
| CommonError | `error_` | `error_hardcoded_values` |
| ExcelFunction | `func_` | `func_index_match` |
| FinancialModel | `model_` | `model_dcf` |
| ModelComponent | `comp_` | `comp_revenue_build` |
| FinancialConcept | `concept_` | `concept_wacc` |
| Shortcut | `shortcut_` | `shortcut_ctrl_shift_enter` |

## Quality Checklist

- [ ] Every entity has `name` and `description` (or `definition`)
- [ ] Every entity has `reference` with book, chapter, pages
- [ ] No orphan entities (all connected via relations)
- [ ] Relations follow schema constraints
- [ ] IDs are unique and follow naming convention
- [ ] Content is original (paraphrased, not copied verbatim)

## Output

After processing, report:

```
✅ Book processed: [Book Name]
   Domain: [excel/econometrics/...]
   Entities added: [N]
   Relations added: [M]
   New coverage: [list of new topics]
   
   Graph updated: ONTOLOGIA/[DOMAIN]/memory/ontology/graph.jsonl
```

## Example Invocation

User: "Procesa el libro CFI-Excel-eBook.pdf para la ontología de Excel"

Agent:
1. Reads `ONTOLOGIA/LIBROS EXCEL/CFI-Excel-eBook.pdf`
2. Reads `ONTOLOGIA/LIBROS EXCEL/memory/ontology/schema.yaml`
3. Extracts entities from each chapter
4. Creates relations between entities
5. Validates against schema
6. Appends to `graph.jsonl`
7. Reports results
