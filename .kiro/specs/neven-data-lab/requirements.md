# Requirements Document

## Introduction

NEVEN Data Lab is a new tab in NEVEN Studio Standalone that exposes NEVEN's analytical function library through a guided, point-and-click interface. The user selects a statistical or machine learning function from a catalog, assigns dataset columns to variable roles, configures parameters, and receives structured results — all without writing code. V1 covers R functions only, with K-Means as the proof-of-concept function.

Data Lab builds on the existing NEVEN Studio infrastructure: the `dataset` table in DuckDB, the Named Pipe connections to ControlR.exe, and the HTTP server already serving `/api/r`, `/api/python`, `/api/julia`. It introduces two new endpoints (`GET /api/datalab/catalog` and `POST /api/datalab/run`) and a sidecar JSON metadata convention for every analytical function in `C:\NEVEN\functions\`.

---

## Glossary

- **Data_Lab**: The new NEVEN Studio tab that is the subject of this document.
- **Catalog**: The collection of all analytical functions discoverable by the Data_Lab, sourced from sidecar JSON files in `C:\NEVEN\functions\`.
- **Sidecar_JSON**: A `.json` file co-located with each `.R` / `.py` / `.jl` function file. It carries the function's id, family, name, description, variable roles, parameters, and output slot definitions.
- **Family**: A functional grouping derived from the function filename prefix (e.g., `AD` = Análisis de Datos, `RG` = Regresión, `GR` = Gráficos).
- **Function_Card**: The metadata object derived from a single Sidecar_JSON, describing one analytical function.
- **Variable_Role**: A named slot (e.g., `X`, `Y`, `T`) that maps one or more dataset columns to a semantic role required by an analytical function.
- **Column_Panel**: The UI component that lists the columns of the currently loaded dataset and allows assignment to Variable_Roles.
- **Parameter_Form**: The UI component that renders input controls for each parameter defined in a Sidecar_JSON.
- **Filter_Box**: A text input that accepts a DuckDB WHERE clause fragment (e.g., `id NOT IN (1, 20, 69)`) applied when querying the dataset before analysis.
- **Run_Button**: The UI control that triggers execution of the selected function with the current configuration.
- **Slot**: A single typed unit of output returned by the serializer. A slot has: `name`, `label`, `type` ∈ {`table`, `scalar`, `vector`, `html`, `text`}, `value`, and `tier` ∈ {1, 2}.
- **Serializer**: An R function (`r_object_to_slots`) that decomposes the native S3 object returned by a Studio wrapper function into a list of Slots.
- **Studio_Wrapper**: An R function (e.g., `AD_KMedias.Studio`) that queries DuckDB, calls the core analytical function, and returns the native result object.
- **Results_Panel**: The UI area that renders all Slots returned by an execution.
- **Tier_1**: Prominent results rendered expanded by default in the Results_Panel.
- **Tier_2**: Technical details rendered collapsed inside a "Detalles técnicos" accordion in the Results_Panel.
- **Migration_Script**: A one-time R script (`migrate_attr_to_json.R`) that reads `attr(fn, "description")` from existing `.R` files and generates an initial Sidecar_JSON for each.
- **DuckDB**: The in-memory SQL database embedded in NEVEN Studio that holds the `dataset` table. Data enters DuckDB through two existing paths: (1) CSV/Parquet/JSON file loading via the Data Studio tab's `/api/load_file` endpoint, or (2) Excel range selection pushed through the Bridge mechanism. The Data_Lab reads from DuckDB but never writes to or modifies the `dataset` table.
- **ControlR**: The ControlR.exe child process that embeds the R runtime and receives code execution requests via Named Pipe.
- **HTTP_Server**: The Python HTTP server in NEVEN Studio Standalone that routes API requests, including the new `/api/datalab/*` endpoints.

---

## Requirements

### Requirement 1: Data Lab Tab

**User Story:** As a NEVEN Studio user, I want a dedicated Data Lab tab in the Studio interface, so that I can access analytical functions without leaving the Studio environment.

#### Acceptance Criteria

1. THE Data_Lab SHALL be accessible as a tab labeled "Data Lab" in `taskpane.html`, positioned after the existing "Run Script" tab.
2. WHEN the user clicks the "Data Lab" tab, THE Data_Lab SHALL display its UI without reloading the page or affecting the state of other tabs.
3. WHILE the Data_Lab tab is active, THE Data_Lab SHALL display the following regions: a function selector area, a Column_Panel, a Parameter_Form, a Filter_Box, a Run_Button, and a Results_Panel.
4. THE Data_Lab SHALL always operate on the `dataset` table already resident in DuckDB — no additional data loading mechanism is provided by the Data_Lab itself. Data reaches DuckDB through one of two existing paths: (a) loading a CSV, Parquet, or JSON file via the Data Studio tab, or (b) pushing an Excel selection via the Bridge mechanism. The Data_Lab reads this table but does not modify it.
5. WHEN the user activates the Data_Lab tab and no `dataset` table exists in DuckDB, THE Data_Lab SHALL display a message instructing the user to load data first via the Data Studio tab or the Excel Bridge, and SHALL disable the Run_Button until a dataset is loaded.

---

### Requirement 2: Function Catalog Discovery

**User Story:** As a NEVEN Studio user, I want the Data Lab to automatically discover available analytical functions, so that I do not need to manually configure which functions are available.

#### Acceptance Criteria

1. THE HTTP_Server SHALL expose a `GET /api/datalab/catalog` endpoint that reads all Sidecar_JSON files from `C:\NEVEN\functions\` and returns a JSON response grouping Function_Cards by language and family.
2. WHEN `GET /api/datalab/catalog` is called, THE HTTP_Server SHALL include in the response only files that have a valid Sidecar_JSON co-located with the corresponding function file.
3. IF a Sidecar_JSON file fails any validation — including invalid JSON syntax, missing required fields (`id`, `family`, `name`, `function_name`, `file`, `languages`, `parameters`), or incorrect field formats — THEN THE HTTP_Server SHALL omit that entry from the catalog response and log a warning with the filename and the reason for rejection.
4. THE HTTP_Server SHALL return the catalog response within 2000 milliseconds of receiving the request, measured from request receipt to response completion.
5. WHEN `GET /api/datalab/catalog` is called and `C:\NEVEN\functions\` contains no valid Sidecar_JSON files, THE HTTP_Server SHALL return an empty catalog with HTTP status 200 regardless of the response time elapsed.

---

### Requirement 3: Family and Function Selection

**User Story:** As a NEVEN Studio user, I want to filter analytical functions by family and then select a specific function, so that I can quickly find the algorithm I need without scrolling through an unmanageable list.

#### Acceptance Criteria

1. THE Data_Lab SHALL display a family dropdown populated from the distinct `family` and `family_label` values present in the catalog response.
2. WHEN the user selects a family from the dropdown, THE Data_Lab SHALL update the function list to show only Function_Cards belonging to the selected family.
3. WHEN the user selects a function from the function list, THE Data_Lab SHALL update the Column_Panel, Parameter_Form, and Filter_Box to reflect the selected function's Sidecar_JSON definition.
4. WHEN the user changes the selected family, THE Data_Lab SHALL clear the current function selection, Column_Panel assignments, Parameter_Form values, and Results_Panel content.
5. THE Data_Lab SHALL display a loading indicator while the catalog is being fetched from `GET /api/datalab/catalog`.
6. IF `GET /api/datalab/catalog` returns an error or fails due to a network error, THEN THE Data_Lab SHALL always display a descriptive error message in the interface and disable the function selector.

---

### Requirement 4: Column Assignment

**User Story:** As a NEVEN Studio user, I want to assign dataset columns to variable roles, so that the analytical function knows which columns to use as inputs.

#### Acceptance Criteria

1. THE Column_Panel SHALL display the column names and inferred types of the currently loaded `dataset` table, fetched from the existing DuckDB introspection API.
2. WHEN a function is selected, THE Column_Panel SHALL render one assignment slot for each Variable_Role defined in the Sidecar_JSON's `variable_roles` object, labeled with the role's `label` value.
3. WHEN a Variable_Role has `"types": ["numeric"]` in the Sidecar_JSON, THE Column_Panel SHALL only allow assignment of columns whose inferred DuckDB type is numeric (INTEGER, DOUBLE, FLOAT, DECIMAL, or BIGINT).
4. THE Column_Panel SHALL allow the user to assign a column to a Variable_Role by clicking the column name in the column list and then clicking the target role slot.
5. WHERE a Variable_Role has `"multiple": true`, THE Column_Panel SHALL allow the user to assign more than one column to that role slot.
6. THE Column_Panel SHALL allow the user to remove a column assignment from a role slot by clicking a remove control on the assigned column chip.
7. WHEN the user clicks Run_Button with one or more required Variable_Roles unassigned, THE Data_Lab SHALL display a validation error in the user's interface language identifying each unfilled required role and SHALL NOT submit the execution request.

---

### Requirement 5: Parameter Form

**User Story:** As a NEVEN Studio user, I want a dynamically generated form for function parameters, so that I can configure the algorithm without reading source code or documentation.

#### Acceptance Criteria

1. WHEN a function is selected, THE Parameter_Form SHALL render one input control per entry in the Sidecar_JSON's `parameters` array, using the parameter's `label` as the visible label.
2. THE Parameter_Form SHALL render the following control types based on parameter `type`: `integer` → numeric spinner, `boolean` → checkbox or toggle, `select` → dropdown populated from the parameter's `options` array.
3. THE Parameter_Form SHALL initialize each control to the parameter's `default` value as defined in the Sidecar_JSON.
4. WHEN a parameter has `"tier": 2`, THE Parameter_Form SHALL render that control inside a collapsible "Parámetros avanzados" section that is collapsed by default and MAY be expanded programmatically or by other UI state without restriction.
5. IF the user enters a non-integer value in a control of type `integer`, THEN THE Parameter_Form SHALL display a validation error on that control and SHALL NOT allow form submission.

---

### Requirement 6: Dataset Filter

**User Story:** As a NEVEN Studio user, I want to apply an optional row filter to the dataset before analysis, so that I can exclude outliers or irrelevant records without permanently modifying the loaded data.

#### Acceptance Criteria

1. THE Data_Lab SHALL display a Filter_Box labeled "Filtro WHERE (opcional)" that accepts free text input.
2. WHEN the Filter_Box is empty and the user clicks Run_Button, THE Data_Lab SHALL execute the analysis on the full `dataset` table without a WHERE clause.
3. WHEN the Filter_Box contains text and the user clicks Run_Button, THE Data_Lab SHALL include the Filter_Box content as the WHERE clause of the DuckDB query that extracts data for the analytical function.
4. IF the Filter_Box content produces a DuckDB query error, THEN THE HTTP_Server SHALL return a structured error response with the DuckDB error message, and THE Data_Lab SHALL display this message in the Results_Panel error area in place of results.

---

### Requirement 7: Execution

**User Story:** As a NEVEN Studio user, I want to run the selected analytical function with one click, so that I receive results immediately without writing any code.

#### Acceptance Criteria

1. THE HTTP_Server SHALL expose a `POST /api/datalab/run` endpoint that accepts a JSON body with fields: `function_id`, `language`, `column_roles`, `parameters`, and `filter_clause`.
2. WHEN `POST /api/datalab/run` is called, THE HTTP_Server SHALL build the R code that: queries DuckDB using the `column_roles` and `filter_clause` fields, calls the Studio_Wrapper function identified by `function_id`, calls `r_object_to_slots` on the result, and returns the slot list as a JSON array.
3. WHEN the user clicks Run_Button and all required Variable_Roles are assigned, THE Data_Lab SHALL POST to `/api/datalab/run` with the current `function_id`, `language`, `column_roles`, `parameters`, and `filter_clause` values, and SHALL display a loading indicator until the response arrives.
4. WHEN Run_Button is clicked, THE Data_Lab SHALL disable Run_Button for the duration of the request and re-enable it after the response is received or an error occurs.
5. IF `POST /api/datalab/run` returns an error from ControlR (R-level error), THEN THE HTTP_Server SHALL return a structured JSON error with `status: "error"` and the R error message, and THE Data_Lab SHALL display this message in the Results_Panel.
6. THE HTTP_Server SHALL forward execution to ControlR using the existing Named Pipe mechanism used by `/api/r`.

---

### Requirement 8: Results Rendering

**User Story:** As a NEVEN Studio user, I want to see the results of an analysis presented in a clear, structured way, so that I can interpret the output without post-processing.

#### Acceptance Criteria

1. WHEN a successful response is received from `POST /api/datalab/run`, THE Results_Panel SHALL render each Slot in the order provided by the Serializer.
2. THE Results_Panel SHALL render Slots according to their `type` field: `table` → paginated HTML table using the existing `data-table` CSS class; `scalar` → `<pre>` element with dark background styling; `vector` → `<pre>` element with dark background styling; `html` → `<iframe>` with `srcdoc` set to the Slot's `value`; `text` → `<pre>` element with dark background styling.
3. WHILE rendering, THE Results_Panel SHALL display the Slot's `label` as a section heading above each rendered Slot.
4. WHEN a Slot has `"tier": 1`, THE Results_Panel SHALL display that Slot expanded by default regardless of other Slots being processed in the same render pass.
5. WHEN a Slot has `"tier": 2`, THE Results_Panel SHALL display that Slot inside a collapsible `<details>` element labeled "Detalles técnicos" that is collapsed by default.
6. THE Results_Panel SHALL clear previous results before rendering new results from a new execution.
7. IF the Slot type is `html` and the value contains an `<iframe>` or script content, THEN THE Results_Panel SHALL render the content using `<iframe srcdoc>` isolation so that interactive htmlwidgets or Plotly outputs function correctly.

---

### Requirement 9: Serializer

**User Story:** As a NEVEN engineer, I want a standard R serializer function, so that every analytical function's native S3 result is decomposed into typed slots without requiring per-function output code.

#### Acceptance Criteria

1. THE Serializer (`r_object_to_slots`) SHALL accept any R S3 object and return a named list of Slots, one per top-level named element of the object.
2. THE Serializer SHALL apply type assignment rules in the following priority order: (1) if the value is a `data.frame` or `matrix`, assign `type = "table"`; (2) else if the value is a character string containing the substring `<html` (case-insensitive), assign `type = "html"`; (3) else if the value is an atomic vector of length greater than 1, assign `type = "vector"`; (4) else if the value is an atomic vector of length 1, assign `type = "scalar"`; (5) else assign `type = "unknown"` for values that match none of the above conditions.
3. THE Serializer SHALL assign `tier = 1` to all Slots by default and SHALL allow overrides via an optional `tier_map` argument (a named integer vector mapping slot name to tier).
4. THE Serializer file (`r_object_to_slots.R`) SHALL be located in the `startup/` directory so that ControlR loads it at startup.
5. FOR ALL valid R S3 objects `obj`, calling `r_object_to_slots(obj)` followed by JSON serialization and deserialization SHALL produce a Slot list where each Slot's `name` matches the corresponding original element name in `names(obj)` (round-trip name preservation).

---

### Requirement 10: Sidecar JSON Schema

**User Story:** As a NEVEN engineer, I want a defined schema for sidecar JSON files, so that function metadata is consistent and machine-readable across all functions.

#### Acceptance Criteria

1. THE Sidecar_JSON SHALL contain the following required fields: `id` (string), `family` (string), `family_label` (string), `name` (string), `description` (string), `languages` (array of strings), `function_name` (string), `file` (string), `variable_roles` (object), `parameters` (array).
2. WHEN a `parameters` entry has `"type": "select"`, THE Sidecar_JSON SHALL include an `options` field in that entry containing an array of objects each with `value` and `label` fields.
3. THE Sidecar_JSON SHALL use the filename convention `{function_file_basename}.json` — the same base name as its companion `.R`, `.py`, or `.jl` file with a `.json` extension.
4. FOR ALL Sidecar_JSON files that the catalog endpoint reads successfully, validating the JSON against the schema and re-serializing it SHALL produce a document with the same field values (round-trip schema stability).

---

### Requirement 11: Migration Script

**User Story:** As a NEVEN engineer, I want a one-time migration script, so that existing R functions with `attr(fn, "description")` metadata are automatically bootstrapped with Sidecar_JSON files.

#### Acceptance Criteria

1. THE Migration_Script (`migrate_attr_to_json.R`) SHALL read each `.R` file in `C:\NEVEN\functions\` that defines functions with `attr(fn, "description")` metadata and generate a corresponding Sidecar_JSON file in the same directory.
2. THE Migration_Script SHALL derive the `family` field from the filename prefix according to the mapping: `R4XCL-AD-*` → `"AD"`, `R4XCL-RG-*` → `"RG"`, `R4XCL-GR-*` → `"GR"`, `R4XCL-MT-*` → `"MT"`, `R4XCL-FX-*` → `"FX"`.
3. THE Migration_Script SHALL populate `description` from the existing `attr(fn, "description")` value when present, and SHALL leave `description` as an empty string when the attribute is absent.
4. THE Migration_Script SHALL set `variable_roles` to an empty object and `parameters` to an empty array in the generated Sidecar_JSON, to be enriched manually after migration.
5. IF a Sidecar_JSON file already exists for a given function file, THEN THE Migration_Script SHALL skip that file and print a message to the console indicating the skip.
6. WHEN the Migration_Script completes, THE Migration_Script SHALL print a summary to the console with the count of files processed, files skipped, and files where generation failed.

---

### Requirement 12: K-Means V1 Function

**User Story:** As a NEVEN Studio user, I want to run K-Means clustering on my dataset, so that I can segment my data into groups without writing R code.

#### Acceptance Criteria

1. THE Catalog SHALL include a Function_Card with `"id": "AD_KMedias"`, `"family": "AD"`, and `"languages": ["r"]`.
2. THE Sidecar_JSON for K-Means SHALL define a Variable_Role `X` with `"label": "Variables activas"`, `"types": ["numeric"]`, `"multiple": true`, and `"required": true`.
3. THE Sidecar_JSON for K-Means SHALL define the following parameters: `K` (integer, default 3, tier 1), `Escala` (boolean, default false, tier 1), `TipoModelo` (select with options Hartigan-Wong/Lloyd/Forgy/MacQueen, default 1, tier 1), `Semilla` (integer, default 123456, tier 2).
4. WHEN the user executes K-Means via Data_Lab, THE HTTP_Server SHALL call `AD_KMedias.Studio` in ControlR with the assigned columns and parameter values.
5. WHEN `AD_KMedias.Studio` returns its result successfully, THE Serializer SHALL produce at minimum a Slot for cluster centers (type `table`) and a Slot for cluster assignments (type `vector`). IF the Studio_Wrapper returns an error, THE Serializer SHALL NOT be called and no Slots SHALL be produced.
6. THE Studio_Wrapper `AD_KMedias.Studio` SHALL NOT include Gap statistic or Elbow computation.

---

### Requirement 13: Language Selection

**User Story:** As a NEVEN Studio user, I want to select the implementation language when a function is available in multiple languages, so that I can use my preferred runtime.

#### Acceptance Criteria

1. WHEN a selected Function_Card has `"languages"` with exactly one entry, THE Data_Lab SHALL set that language silently without displaying a language selector.
2. WHEN a selected Function_Card has `"languages"` with more than one entry, THE Data_Lab SHALL display a language selector dropdown populated with the available languages. IF the language selector cannot be rendered, THE Data_Lab SHALL allow execution to proceed using the first language in the `languages` array as the default.
3. THE Data_Lab SHALL include the selected `language` value in the `POST /api/datalab/run` request body.
4. WHERE the selected language is `"r"`, THE HTTP_Server SHALL route the execution request to ControlR via the existing Named Pipe mechanism.

---

### Requirement 14: Error Handling and Resilience

**User Story:** As a NEVEN Studio user, I want clear error messages when something goes wrong, so that I can diagnose and correct the problem without needing developer tools.

#### Acceptance Criteria

1. IF ControlR is not running when `POST /api/datalab/run` is called, THEN THE HTTP_Server SHALL return a structured JSON error with `status: "error"` and a message in Spanish indicating the engine is unavailable.
2. IF the DuckDB filter clause is syntactically invalid, THEN THE HTTP_Server SHALL return a structured JSON error containing the DuckDB error message before attempting R execution.
3. IF a required Variable_Role has no column assigned when the user clicks Run_Button, THEN THE Data_Lab SHALL display a validation message in Spanish identifying the missing role and SHALL NOT send the request to the server.
4. IF `GET /api/datalab/catalog` fails due to a network error, THEN THE Data_Lab SHALL display the error message in the interface and render a retry button that re-issues the catalog request when clicked.
5. WHEN an error occurs in any Data_Lab operation, THE Data_Lab SHALL display the error message in the Results_Panel error area rather than in a browser alert dialog. IF the Results_Panel is unavailable or fails to render, THE Data_Lab SHALL fall back to a browser alert dialog to ensure the error is visible to the user.
