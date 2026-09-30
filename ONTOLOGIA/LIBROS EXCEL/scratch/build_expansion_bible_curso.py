"""
Build expansion for Excel ontology from:
1. Curso Práctico Paso a Paso (341 pages, Spanish)
2. Microsoft Excel 365 Bible (1074 pages, English)

Appends new entities and relations to existing graph.jsonl
"""
import json

# New entities from both books
new_entities = [
    # ═══════════════════════════════════════════════════════════════════════════
    # DOMAINS - New book sources
    # ═══════════════════════════════════════════════════════════════════════════
    {
        "id": "domain_curso_practico",
        "type": "Domain",
        "properties": {
            "name": "Curso Práctico Excel 2019-365",
            "description": "Curso completo paso a paso desde cero hasta nivel avanzado. Enfoque didáctico en español con ejercicios prácticos.",
            "source_book": "Excel 2019-365: Curso Práctico Paso a Paso",
            "chapters": ["Fundamentos", "Fórmulas", "Funciones", "Gráficos", "Tablas Dinámicas", "Macros"]
        }
    },
    {
        "id": "domain_excel_bible",
        "type": "Domain",
        "properties": {
            "name": "Microsoft Excel 365 Bible",
            "description": "Comprehensive Excel reference covering all features from basics to advanced programming. The definitive Excel resource with 1074 pages.",
            "source_book": "Microsoft Excel 365 Bible",
            "chapters": ["Getting Started", "Formulas and Functions", "Charts", "Data Analysis", "Collaboration", "Automation"]
        }
    },
    
    # ═══════════════════════════════════════════════════════════════════════════
    # TECHNIQUES - From Excel Bible
    # ═══════════════════════════════════════════════════════════════════════════
    {
        "id": "technique_autofill",
        "type": "Technique",
        "properties": {
            "name": "AutoFill for Series",
            "description": "Using the fill handle to automatically extend a series of values, dates, or custom lists. Excel recognizes patterns and continues them.",
            "steps": ["Select cell(s) with initial value(s)", "Point to fill handle (small square at bottom-right)", "Drag to extend series", "Use AutoFill Options for variations"],
            "use_cases": ["Date series", "Number sequences", "Day/month names", "Custom lists"],
            "reference": {"book": "Excel 365 Bible", "chapter": "Chapter 2: Entering and Editing Worksheet Data", "pages": "p. 83"}
        }
    },
    {
        "id": "technique_autocomplete",
        "type": "Technique",
        "properties": {
            "name": "AutoComplete for Data Entry",
            "description": "Excel automatically suggests completions based on existing entries in the same column. Press Enter to accept or keep typing to ignore.",
            "steps": ["Start typing in a cell", "If match found, suggestion appears", "Press Enter to accept", "Press Delete to clear and type different value"],
            "use_cases": ["Repetitive data entry", "Consistent spelling", "Category columns"],
            "reference": {"book": "Excel 365 Bible", "chapter": "Chapter 2", "pages": "p. 83-84"}
        }
    },
    {
        "id": "technique_data_entry_form",
        "type": "Technique",
        "properties": {
            "name": "Data Entry Form",
            "description": "Built-in form for entering data into a list or table. Shows one record at a time with field labels from headers.",
            "steps": ["Select any cell in data range", "Add Form command to Quick Access Toolbar", "Click Form button", "Enter data in fields", "Click New for next record"],
            "use_cases": ["Large datasets", "Consistent data entry", "Reducing entry errors"],
            "reference": {"book": "Excel 365 Bible", "chapter": "Chapter 2", "pages": "p. 86-87"}
        }
    },
    {
        "id": "technique_flash_fill",
        "type": "Technique",
        "properties": {
            "name": "Flash Fill",
            "description": "Excel learns patterns from examples you type and automatically fills remaining cells. Works for text manipulation, formatting, and extraction.",
            "steps": ["Type example of desired result in adjacent column", "Type second example if needed", "Press Ctrl+E or Data > Flash Fill", "Excel fills remaining cells"],
            "use_cases": ["Name splitting/combining", "Phone number formatting", "Extracting parts of text", "Reformatting data"],
            "excel_version": "Excel 2013+",
            "reference": {"book": "Excel 365 Bible", "chapter": "Chapter 2", "pages": "implicit"}
        }
    },
    {
        "id": "technique_custom_number_format",
        "type": "Technique",
        "properties": {
            "name": "Custom Number Formats",
            "description": "Create custom display formats using format codes. Doesn't change the underlying value, only how it appears.",
            "steps": ["Select cells", "Ctrl+1 for Format Cells", "Number tab > Custom", "Enter format code", "OK"],
            "use_cases": ["Phone numbers", "Social security numbers", "Custom date formats", "Conditional colors", "Adding text to numbers"],
            "reference": {"book": "Excel 365 Bible", "chapter": "Chapter 2", "pages": "p. 93"}
        }
    },
    {
        "id": "technique_freeze_panes",
        "type": "Technique",
        "properties": {
            "name": "Freeze Panes",
            "description": "Keep row and column headers visible while scrolling through large datasets.",
            "steps": ["Click cell below rows and right of columns to freeze", "View > Freeze Panes > Freeze Panes", "Or use Freeze Top Row / Freeze First Column"],
            "use_cases": ["Large datasets", "Keeping headers visible", "Comparing distant data"],
            "reference": {"book": "Excel 365 Bible", "chapter": "Chapter 3", "pages": "implicit"}
        }
    },
    {
        "id": "technique_name_manager",
        "type": "Technique",
        "properties": {
            "name": "Named Ranges with Name Manager",
            "description": "Assign meaningful names to cells or ranges for easier formula creation and maintenance.",
            "steps": ["Select range", "Formulas > Define Name", "Enter name and scope", "Use name in formulas"],
            "use_cases": ["Self-documenting formulas", "Easier maintenance", "Dynamic ranges", "Input cells"],
            "reference": {"book": "Excel 365 Bible", "chapter": "Formulas", "pages": "implicit"}
        }
    },
    {
        "id": "technique_data_validation",
        "type": "Technique",
        "properties": {
            "name": "Data Validation",
            "description": "Restrict what users can enter in cells. Create dropdown lists, number ranges, date limits, and custom validation rules.",
            "steps": ["Select input cells", "Data > Data Validation", "Choose validation type", "Set criteria", "Optional: Input message and error alert"],
            "use_cases": ["Dropdown lists", "Date ranges", "Number limits", "Preventing errors", "User guidance"],
            "reference": {"book": "Excel 365 Bible", "chapter": "Data Analysis", "pages": "implicit"}
        }
    },
    {
        "id": "technique_conditional_formatting",
        "type": "Technique",
        "properties": {
            "name": "Conditional Formatting",
            "description": "Apply formatting (colors, icons, data bars) based on cell values or formulas. Makes patterns and outliers visible at a glance.",
            "steps": ["Select range", "Home > Conditional Formatting", "Choose rule type", "Define conditions", "Set format"],
            "use_cases": ["Heat maps", "Highlighting outliers", "Progress indicators", "Data bars", "Icon sets"],
            "reference": {"book": "Excel 365 Bible", "chapter": "Formatting", "pages": "implicit"}
        }
    },
    {
        "id": "technique_pivot_table",
        "type": "Technique",
        "properties": {
            "name": "PivotTable Analysis",
            "description": "Summarize, analyze, and explore large datasets interactively. Drag fields to rows, columns, values, and filters.",
            "steps": ["Select data range", "Insert > PivotTable", "Choose location", "Drag fields to areas", "Configure value calculations"],
            "use_cases": ["Data summarization", "Cross-tabulation", "Grouping", "Filtering", "Ad-hoc analysis"],
            "reference": {"book": "Excel 365 Bible", "chapter": "PivotTables", "pages": "implicit"}
        }
    },
    {
        "id": "technique_power_query",
        "type": "Technique",
        "properties": {
            "name": "Power Query (Get & Transform)",
            "description": "Import, clean, and transform data from multiple sources. Create repeatable data preparation steps.",
            "steps": ["Data > Get Data > choose source", "Select data", "Transform in Power Query Editor", "Close & Load"],
            "use_cases": ["Data import", "Data cleaning", "Combining sources", "Repeatable ETL", "Text transformations"],
            "excel_version": "Excel 2016+",
            "reference": {"book": "Excel 365 Bible", "chapter": "Power Query", "pages": "implicit"}
        }
    },
    
    # ═══════════════════════════════════════════════════════════════════════════
    # TECHNIQUES - From Curso Práctico (Spanish perspectives)
    # ═══════════════════════════════════════════════════════════════════════════
    {
        "id": "technique_formato_condicional_semaforo",
        "type": "Technique",
        "properties": {
            "name": "Formato Condicional Semáforo",
            "description": "Usar iconos de semáforo (verde/amarillo/rojo) para indicar estado de KPIs o métricas. Visualización intuitiva del desempeño.",
            "steps": ["Seleccionar rango", "Formato condicional > Conjunto de iconos", "Elegir semáforo", "Ajustar umbrales"],
            "use_cases": ["Dashboards", "KPIs", "Estado de proyectos", "Métricas de ventas"],
            "reference": {"book": "Curso Práctico Excel 2019-365", "chapter": "Formato Condicional", "pages": "implicit"}
        }
    },
    {
        "id": "technique_tablas_excel",
        "type": "Technique",
        "properties": {
            "name": "Tablas de Excel (Ctrl+T)",
            "description": "Convertir rango en tabla estructurada. Obtiene nombres de columna, filtros automáticos, formato alternado, y referencias estructuradas.",
            "steps": ["Seleccionar datos", "Ctrl+T o Insertar > Tabla", "Confirmar rango y encabezados", "Usar referencias estructuradas en fórmulas"],
            "use_cases": ["Datos dinámicos", "Auto-expansión de fórmulas", "Filtrado rápido", "Diseño consistente"],
            "reference": {"book": "Curso Práctico Excel 2019-365", "chapter": "Tablas", "pages": "implicit"}
        }
    },
    
    # ═══════════════════════════════════════════════════════════════════════════
    # BEST PRACTICES - From Excel Bible
    # ═══════════════════════════════════════════════════════════════════════════
    {
        "id": "bp_structured_references",
        "type": "BestPractice",
        "properties": {
            "name": "Use Structured References in Tables",
            "description": "When working with Excel Tables, use structured references like [@Column] instead of cell addresses. Formulas become self-documenting.",
            "rationale": "Structured references are readable, maintain meaning when rows/columns move, and auto-expand with table.",
            "examples": ["=SUM(Table1[Sales])", "=[@Price]*[@Quantity]", "=SUMIF(Table1[Region],\"North\",Table1[Revenue])"],
            "reference": {"book": "Excel 365 Bible", "chapter": "Tables", "pages": "implicit"}
        }
    },
    {
        "id": "bp_separate_inputs_calcs",
        "type": "BestPractice",
        "properties": {
            "name": "Separate Inputs from Calculations",
            "description": "Create a dedicated section for all input assumptions, separate from calculation cells. Use different background colors to distinguish.",
            "rationale": "Makes models easier to audit, update, and understand. Changes to assumptions are centralized.",
            "examples": ["Blue fill for inputs", "Yellow fill for linked cells", "No fill for calculations"],
            "anti_pattern": "Hardcoding values directly in formulas throughout the workbook",
            "reference": {"book": "Excel 365 Bible", "chapter": "Best Practices", "pages": "implicit"}
        }
    },
    {
        "id": "bp_document_formulas",
        "type": "BestPractice",
        "properties": {
            "name": "Document Complex Formulas",
            "description": "Add comments or adjacent cells explaining complex formulas. Use named ranges to make formulas self-documenting.",
            "rationale": "Future users (including yourself) need to understand formula logic. Documentation reduces maintenance time.",
            "examples": ["=Revenue-COGS 'Gross Profit", "Named range: GrossMargin = Revenue-COGS"],
            "reference": {"book": "Excel 365 Bible", "chapter": "Best Practices", "pages": "implicit"}
        }
    },
    {
        "id": "bp_error_handling",
        "type": "BestPractice",
        "properties": {
            "name": "Implement Error Handling",
            "description": "Wrap formulas that might produce errors in IFERROR or IFNA. Provide meaningful defaults or messages.",
            "rationale": "Prevents #VALUE!, #N/A, #DIV/0! from cascading through workbook. Makes models robust to missing data.",
            "examples": ["=IFERROR(VLOOKUP(...), 0)", "=IFERROR(A1/B1, \"N/A\")"],
            "anti_pattern": "Leaving error values visible in reports",
            "reference": {"book": "Excel 365 Bible", "chapter": "Formulas", "pages": "implicit"}
        }
    },
    {
        "id": "bp_use_tables",
        "type": "BestPractice",
        "properties": {
            "name": "Convert Data Ranges to Tables",
            "description": "Use Ctrl+T to convert data ranges to proper Excel Tables. Enables auto-expansion, structured references, and better PivotTable integration.",
            "rationale": "Tables auto-expand with new data, formulas copy automatically, and structured references are clearer than A1 notation.",
            "examples": ["Ctrl+T on data range", "Table1[ColumnName] references"],
            "reference": {"book": "Excel 365 Bible", "chapter": "Tables", "pages": "implicit"}
        }
    },
    
    # ═══════════════════════════════════════════════════════════════════════════
    # COMMON ERRORS - From Excel Bible
    # ═══════════════════════════════════════════════════════════════════════════
    {
        "id": "error_volatile_functions",
        "type": "CommonError",
        "properties": {
            "name": "Overusing Volatile Functions",
            "description": "Functions like INDIRECT, OFFSET, NOW, TODAY, RAND recalculate every time anything changes, slowing down large workbooks.",
            "cause": "Using INDIRECT for dynamic ranges, multiple OFFSET calls, or unnecessary NOW/TODAY",
            "solution": "Replace INDIRECT with INDEX, OFFSET with INDEX+MATCH, limit volatile functions",
            "prevention": "Prefer non-volatile alternatives: INDEX instead of OFFSET, table references instead of INDIRECT",
            "reference": {"book": "Excel 365 Bible", "chapter": "Performance", "pages": "implicit"}
        }
    },
    {
        "id": "error_merged_cells",
        "type": "CommonError",
        "properties": {
            "name": "Merging Cells in Data Ranges",
            "description": "Merged cells break sorting, filtering, PivotTables, and many formulas. Avoid in data areas.",
            "cause": "Using Merge & Center for visual formatting in data tables",
            "solution": "Use Center Across Selection instead, or format headers separately from data",
            "prevention": "Never merge cells in data ranges. Use for titles only, outside data areas.",
            "reference": {"book": "Excel 365 Bible", "chapter": "Data Analysis", "pages": "implicit"}
        }
    },
    {
        "id": "error_array_formula_legacy",
        "type": "CommonError",
        "properties": {
            "name": "Using Legacy Array Formulas (Ctrl+Shift+Enter)",
            "description": "In Excel 365/2021, many array formulas work without CSE. Using CSE unnecessarily can cause confusion.",
            "cause": "Old habits from earlier Excel versions",
            "solution": "In Excel 365, just press Enter. Dynamic arrays spill automatically.",
            "prevention": "Learn dynamic array syntax: FILTER, SORT, UNIQUE, SEQUENCE",
            "reference": {"book": "Excel 365 Bible", "chapter": "Dynamic Arrays", "pages": "implicit"}
        }
    },
    {
        "id": "error_wrong_reference_type",
        "type": "CommonError",
        "properties": {
            "name": "Wrong Reference Type When Copying",
            "description": "Using relative references when absolute are needed, or vice versa. Formulas break when copied.",
            "cause": "Not considering how formula will be copied, not using F4 to toggle",
            "solution": "Use F4 while editing to cycle through reference types: A1 → $A$1 → A$1 → $A1",
            "prevention": "Think about copy direction before creating formula. Lock what shouldn't change.",
            "reference": {"book": "Excel 365 Bible", "chapter": "Formulas", "pages": "implicit"}
        }
    },
    
    # ═══════════════════════════════════════════════════════════════════════════
    # EXCEL FUNCTIONS - New functions from Bible (not in CFI book)
    # ═══════════════════════════════════════════════════════════════════════════
    {
        "id": "func_filter",
        "type": "ExcelFunction",
        "properties": {
            "name": "FILTER",
            "category": "Lookup and reference",
            "description": "Returns an array of values that meet criteria. Dynamic array function that spills results.",
            "syntax": "=FILTER(array, include, [if_empty])",
            "best_practices": ["Use with other dynamic array functions", "Provide if_empty for no matches", "Combine conditions with *"],
            "common_errors": ["Forgetting if_empty causes #CALC! when no matches"],
            "reference": {"book": "Excel 365 Bible", "chapter": "Dynamic Arrays", "pages": "implicit"}
        }
    },
    {
        "id": "func_sort",
        "type": "ExcelFunction",
        "properties": {
            "name": "SORT",
            "category": "Lookup and reference",
            "description": "Sorts the contents of a range or array. Returns a dynamic array.",
            "syntax": "=SORT(array, [sort_index], [sort_order], [by_col])",
            "best_practices": ["Combine with FILTER for filtered+sorted results", "Use -1 for descending"],
            "reference": {"book": "Excel 365 Bible", "chapter": "Dynamic Arrays", "pages": "implicit"}
        }
    },
    {
        "id": "func_unique",
        "type": "ExcelFunction",
        "properties": {
            "name": "UNIQUE",
            "category": "Lookup and reference",
            "description": "Returns a list of unique values from a range or array.",
            "syntax": "=UNIQUE(array, [by_col], [exactly_once])",
            "best_practices": ["Use for dropdown lists", "Combine with SORT for sorted unique list"],
            "reference": {"book": "Excel 365 Bible", "chapter": "Dynamic Arrays", "pages": "implicit"}
        }
    },
    {
        "id": "func_sequence",
        "type": "ExcelFunction",
        "properties": {
            "name": "SEQUENCE",
            "category": "Math and trigonometry",
            "description": "Generates a sequence of numbers. Useful for creating arrays without helper columns.",
            "syntax": "=SEQUENCE(rows, [columns], [start], [step])",
            "best_practices": ["Use with INDEX for array formulas", "Generate date series", "Create row numbers"],
            "reference": {"book": "Excel 365 Bible", "chapter": "Dynamic Arrays", "pages": "implicit"}
        }
    },
    {
        "id": "func_xlookup",
        "type": "ExcelFunction",
        "properties": {
            "name": "XLOOKUP",
            "category": "Lookup and reference",
            "description": "Modern replacement for VLOOKUP/HLOOKUP. Can look in any direction, return arrays, and has better error handling.",
            "syntax": "=XLOOKUP(lookup_value, lookup_array, return_array, [if_not_found], [match_mode], [search_mode])",
            "best_practices": ["Use instead of VLOOKUP for new work", "Built-in if_not_found replaces IFERROR", "Can return multiple columns"],
            "common_errors": ["Not available in older Excel versions"],
            "reference": {"book": "Excel 365 Bible", "chapter": "Lookup Functions", "pages": "implicit"}
        }
    },
    {
        "id": "func_let",
        "type": "ExcelFunction",
        "properties": {
            "name": "LET",
            "category": "Logical",
            "description": "Assigns names to calculation results within a formula. Improves readability and performance by avoiding repeated calculations.",
            "syntax": "=LET(name1, value1, [name2, value2, ...], calculation)",
            "best_practices": ["Name intermediate results", "Avoid repeating complex expressions", "Makes formulas self-documenting"],
            "reference": {"book": "Excel 365 Bible", "chapter": "Advanced Formulas", "pages": "implicit"}
        }
    },
    {
        "id": "func_lambda",
        "type": "ExcelFunction",
        "properties": {
            "name": "LAMBDA",
            "category": "Logical",
            "description": "Creates custom functions without VBA. Define parameters and calculation, then assign to a name.",
            "syntax": "=LAMBDA([parameter1, parameter2, ...], calculation)",
            "best_practices": ["Store in Name Manager for reuse", "Document parameters clearly", "Use with MAP, REDUCE, SCAN"],
            "reference": {"book": "Excel 365 Bible", "chapter": "LAMBDA Functions", "pages": "implicit"}
        }
    },
    {
        "id": "func_textsplit",
        "type": "ExcelFunction",
        "properties": {
            "name": "TEXTSPLIT",
            "category": "Text",
            "description": "Splits text by column and/or row delimiters. Returns dynamic array.",
            "syntax": "=TEXTSPLIT(text, col_delimiter, [row_delimiter], [ignore_empty], [match_mode], [pad_with])",
            "best_practices": ["Replace Text to Columns for repeatable splits", "Combine with other dynamic arrays"],
            "reference": {"book": "Excel 365 Bible", "chapter": "Text Functions", "pages": "implicit"}
        }
    },
    {
        "id": "func_textjoin",
        "type": "ExcelFunction",
        "properties": {
            "name": "TEXTJOIN",
            "category": "Text",
            "description": "Joins text from multiple ranges with a delimiter. Can ignore empty cells.",
            "syntax": "=TEXTJOIN(delimiter, ignore_empty, text1, [text2], ...)",
            "best_practices": ["Better than CONCATENATE for lists", "Use TRUE to skip blanks"],
            "reference": {"book": "Excel 365 Bible", "chapter": "Text Functions", "pages": "implicit"}
        }
    },
    {
        "id": "func_ifs_switch",
        "type": "ExcelFunction",
        "properties": {
            "name": "SWITCH",
            "category": "Logical",
            "description": "Evaluates an expression against a list of values and returns the result for the first match.",
            "syntax": "=SWITCH(expression, value1, result1, [value2, result2, ...], [default])",
            "best_practices": ["Cleaner than nested IF for multiple exact matches", "Include default for no match"],
            "reference": {"book": "Excel 365 Bible", "chapter": "Logical Functions", "pages": "implicit"}
        }
    },
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PATTERNS - Advanced patterns from Bible
    # ═══════════════════════════════════════════════════════════════════════════
    {
        "id": "pattern_dynamic_arrays",
        "type": "Pattern",
        "properties": {
            "name": "Dynamic Array Formulas Pattern",
            "description": "Combining FILTER, SORT, UNIQUE, and other dynamic array functions to create powerful data transformations without helper columns.",
            "example": "=SORT(UNIQUE(FILTER(Data[Region], Data[Sales]>1000)))",
            "functions_used": ["FILTER", "SORT", "UNIQUE", "SEQUENCE"],
            "use_cases": ["Dynamic dropdowns", "Filtered reports", "Sorted unique lists"],
            "reference": {"book": "Excel 365 Bible", "chapter": "Dynamic Arrays", "pages": "implicit"}
        }
    },
    {
        "id": "pattern_xlookup_multiple",
        "type": "Pattern",
        "properties": {
            "name": "XLOOKUP Returning Multiple Columns",
            "description": "Using XLOOKUP to return entire rows or multiple columns at once, replacing multiple VLOOKUP formulas.",
            "example": "=XLOOKUP(A1, Products[ID], Products[Name]:Products[Price])",
            "functions_used": ["XLOOKUP"],
            "use_cases": ["Multi-column lookups", "Replacing INDEX/MATCH arrays", "Efficient data retrieval"],
            "reference": {"book": "Excel 365 Bible", "chapter": "Lookup Functions", "pages": "implicit"}
        }
    },
    {
        "id": "pattern_let_complex",
        "type": "Pattern",
        "properties": {
            "name": "LET for Complex Calculations",
            "description": "Using LET to name intermediate results in complex formulas, improving readability and performance.",
            "example": "=LET(revenue, SUM(Sales), costs, SUM(Expenses), margin, revenue-costs, IF(margin>0, margin/revenue, 0))",
            "functions_used": ["LET"],
            "use_cases": ["Financial calculations", "Nested logic", "Performance optimization"],
            "reference": {"book": "Excel 365 Bible", "chapter": "Advanced Formulas", "pages": "implicit"}
        }
    },
]

# New relations
new_relations = [
    # Domains part_of main domain
    {"op": "relate", "from": "domain_curso_practico", "rel": "part_of", "to": "domain_cfi_excel"},
    {"op": "relate", "from": "domain_excel_bible", "rel": "part_of", "to": "domain_cfi_excel"},
    
    # Techniques part_of domains
    {"op": "relate", "from": "technique_autofill", "rel": "part_of", "to": "domain_excel_bible"},
    {"op": "relate", "from": "technique_autocomplete", "rel": "part_of", "to": "domain_excel_bible"},
    {"op": "relate", "from": "technique_data_entry_form", "rel": "part_of", "to": "domain_excel_bible"},
    {"op": "relate", "from": "technique_flash_fill", "rel": "part_of", "to": "domain_excel_bible"},
    {"op": "relate", "from": "technique_custom_number_format", "rel": "part_of", "to": "domain_excel_bible"},
    {"op": "relate", "from": "technique_freeze_panes", "rel": "part_of", "to": "domain_excel_bible"},
    {"op": "relate", "from": "technique_name_manager", "rel": "part_of", "to": "domain_excel_bible"},
    {"op": "relate", "from": "technique_data_validation", "rel": "part_of", "to": "domain_excel_bible"},
    {"op": "relate", "from": "technique_conditional_formatting", "rel": "part_of", "to": "domain_excel_bible"},
    {"op": "relate", "from": "technique_pivot_table", "rel": "part_of", "to": "domain_excel_bible"},
    {"op": "relate", "from": "technique_power_query", "rel": "part_of", "to": "domain_excel_bible"},
    {"op": "relate", "from": "technique_formato_condicional_semaforo", "rel": "part_of", "to": "domain_curso_practico"},
    {"op": "relate", "from": "technique_tablas_excel", "rel": "part_of", "to": "domain_curso_practico"},
    
    # Best practices part_of
    {"op": "relate", "from": "bp_structured_references", "rel": "part_of", "to": "domain_excel_bible"},
    {"op": "relate", "from": "bp_separate_inputs_calcs", "rel": "part_of", "to": "domain_excel_bible"},
    {"op": "relate", "from": "bp_document_formulas", "rel": "part_of", "to": "domain_excel_bible"},
    {"op": "relate", "from": "bp_error_handling", "rel": "part_of", "to": "domain_excel_bible"},
    {"op": "relate", "from": "bp_use_tables", "rel": "part_of", "to": "domain_excel_bible"},
    
    # Errors part_of
    {"op": "relate", "from": "error_volatile_functions", "rel": "part_of", "to": "domain_excel_bible"},
    {"op": "relate", "from": "error_merged_cells", "rel": "part_of", "to": "domain_excel_bible"},
    {"op": "relate", "from": "error_array_formula_legacy", "rel": "part_of", "to": "domain_excel_bible"},
    {"op": "relate", "from": "error_wrong_reference_type", "rel": "part_of", "to": "domain_excel_bible"},
    
    # Functions part_of
    {"op": "relate", "from": "func_filter", "rel": "part_of", "to": "domain_excel_bible"},
    {"op": "relate", "from": "func_sort", "rel": "part_of", "to": "domain_excel_bible"},
    {"op": "relate", "from": "func_unique", "rel": "part_of", "to": "domain_excel_bible"},
    {"op": "relate", "from": "func_sequence", "rel": "part_of", "to": "domain_excel_bible"},
    {"op": "relate", "from": "func_xlookup", "rel": "part_of", "to": "domain_excel_bible"},
    {"op": "relate", "from": "func_let", "rel": "part_of", "to": "domain_excel_bible"},
    {"op": "relate", "from": "func_lambda", "rel": "part_of", "to": "domain_excel_bible"},
    {"op": "relate", "from": "func_textsplit", "rel": "part_of", "to": "domain_excel_bible"},
    {"op": "relate", "from": "func_textjoin", "rel": "part_of", "to": "domain_excel_bible"},
    {"op": "relate", "from": "func_ifs_switch", "rel": "part_of", "to": "domain_excel_bible"},
    
    # Patterns part_of
    {"op": "relate", "from": "pattern_dynamic_arrays", "rel": "part_of", "to": "domain_excel_bible"},
    {"op": "relate", "from": "pattern_xlookup_multiple", "rel": "part_of", "to": "domain_excel_bible"},
    {"op": "relate", "from": "pattern_let_complex", "rel": "part_of", "to": "domain_excel_bible"},
    
    # Patterns use functions
    {"op": "relate", "from": "pattern_dynamic_arrays", "rel": "uses_function", "to": "func_filter"},
    {"op": "relate", "from": "pattern_dynamic_arrays", "rel": "uses_function", "to": "func_sort"},
    {"op": "relate", "from": "pattern_dynamic_arrays", "rel": "uses_function", "to": "func_unique"},
    {"op": "relate", "from": "pattern_xlookup_multiple", "rel": "uses_function", "to": "func_xlookup"},
    {"op": "relate", "from": "pattern_let_complex", "rel": "uses_function", "to": "func_let"},
    
    # Best practices prevent errors
    {"op": "relate", "from": "bp_error_handling", "rel": "prevents", "to": "error_hardcoded_values"},
    {"op": "relate", "from": "bp_separate_inputs_calcs", "rel": "prevents", "to": "error_hardcoded_values"},
    {"op": "relate", "from": "bp_use_tables", "rel": "prevents", "to": "error_merged_cells"},
    
    # Alternative functions
    {"op": "relate", "from": "func_xlookup", "rel": "alternative_to", "to": "func_vlookup"},
    {"op": "relate", "from": "func_xlookup", "rel": "alternative_to", "to": "func_hlookup"},
    {"op": "relate", "from": "func_ifs_switch", "rel": "alternative_to", "to": "func_if"},
    {"op": "relate", "from": "func_textjoin", "rel": "alternative_to", "to": "func_concatenate"},
    
    # Techniques improve other techniques
    {"op": "relate", "from": "technique_name_manager", "rel": "improves", "to": "technique_data_validation"},
    {"op": "relate", "from": "technique_tablas_excel", "rel": "improves", "to": "technique_pivot_table"},
]

# Read existing graph
existing_lines = []
with open(r'F:\ANTIGRAVITY\2026\NEVEN\ONTOLOGIA\LIBROS EXCEL\memory\ontology\graph.jsonl', 'r', encoding='utf-8') as f:
    existing_lines = f.readlines()

print(f"Existing graph: {len(existing_lines)} lines")

# Append new entities and relations
with open(r'F:\ANTIGRAVITY\2026\NEVEN\ONTOLOGIA\LIBROS EXCEL\memory\ontology\graph.jsonl', 'a', encoding='utf-8') as f:
    for ent in new_entities:
        f.write(json.dumps({"op": "create", "entity": ent}, ensure_ascii=False) + '\n')
    for rel in new_relations:
        f.write(json.dumps(rel, ensure_ascii=False) + '\n')

print(f"Added: {len(new_entities)} entities, {len(new_relations)} relations")
print(f"New total: {len(existing_lines) + len(new_entities) + len(new_relations)} lines")
