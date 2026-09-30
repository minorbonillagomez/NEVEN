# Implementation Plan: NEVEN v3.0 Task Pane

## Overview

Este plan implementa el Task Pane de NEVEN v3.0 en 23 tareas atómicas organizadas en 6 fases.
Cada fase construye sobre la anterior: servidor HTTP → manifiesto → bridge Office.js → API DuckDB → UI → despliegue.
Cubre los 13 requisitos del documento de requerimientos.

## Tasks

### Phase 1: HTTP Server Foundation

- [ ] 1. Create HTTP server module skeleton (neven_http_server.py) with port binding (5555/5556 fallback) and daemon thread start
  - **Requirements:** Req 2
  - **Design Reference:** §2.2 (HTTP Server)
  - **Files:** Create `ControlPython/startup/neven_http_server.py`
  - **Acceptance:** Server binds to 5555; falls back to 5556 if occupied; logs FATAL if both unavailable

- [ ] 2. Add HTTPS with self-signed certificate via Python ssl module
  - **Requirements:** Req 2
  - **Design Reference:** §2.2 (HTTPS Configuration)
  - **Files:** Modify `ControlPython/startup/neven_http_server.py`
  - **Acceptance:** `curl --insecure https://localhost:5555/health` succeeds; plain HTTP rejected

- [ ] 3. Implement CORS headers on all responses and /health endpoint returning JSON status
  - **Requirements:** Req 2
  - **Design Reference:** §2.2 (CORS Configuration, Endpoints)
  - **Files:** Modify `ControlPython/startup/neven_http_server.py`
  - **Acceptance:** OPTIONS returns CORS headers; GET /health returns `{"status":"ok","version":"3.0.0"}`

- [ ] 4. Implement static file serving (staticDir + viewersDir) and rate limiter (60 req/min)
  - **Requirements:** Req 2, Req 11, Req 13
  - **Design Reference:** §2.2 (Endpoints), Security (Rate Limiting)
  - **Files:** Modify `ControlPython/startup/neven_http_server.py`
  - **Acceptance:** GET /taskpane.html serves file; GET /viewers/dashboard.html works; 61st rapid request returns 429; oversized POST returns 413

### Phase 2: manifest.xml + Task Pane Shell

- [ ] 5. Create Office Web Add-in manifest.xml (schema v1.1, TaskPaneApp, EquivalentAddins for XLL)
  - **Requirements:** Req 1, Req 9
  - **Design Reference:** §2.1 (manifest.xml)
  - **Files:** Create `TaskPane/manifest.xml`
  - **Acceptance:** Manifest validates against Office Add-in XSD; contains Id, DisplayName "NEVEN Studio", Host Workbook, SourceLocation https://localhost:5555/taskpane.html, EquivalentAddins NEVEN64.xll

- [ ] 6. Create Task Pane HTML shell with three-tab layout (Data Studio, Viewers, SQL) and status bar
  - **Requirements:** Req 3, Req 5, Req 6, Req 7, Req 8, Req 11
  - **Design Reference:** §2.3 (UI Structure)
  - **Files:** Create `TaskPane/taskpane.html`, Create `TaskPane/taskpane.css`
  - **Acceptance:** HTML renders three tabs that switch content areas; status bar visible; ARIA labels present; no console errors

- [ ] 7. Create add-in icons (32×32, 64×64 PNG) and bundle Chart.js for bar charts
  - **Requirements:** Req 1
  - **Design Reference:** §File Structure (New Files)
  - **Files:** Create `TaskPane/assets/icon-32.png`, Create `TaskPane/assets/icon-64.png`, Create `TaskPane/chart.min.js`
  - **Acceptance:** Icons are valid PNG at correct dimensions; chart.min.js loads and exposes Chart constructor

### Phase 3: Office.js Bridge

- [ ] 8. Implement Office.onReady initialization and onSelectionChanged event handler with status bar updates
  - **Requirements:** Req 5
  - **Design Reference:** §2.3 (Office.js Initialization, Selection Change)
  - **Files:** Create `TaskPane/taskpane.js`
  - **Acceptance:** Status bar updates within 200ms on selection change; Auto-load ON reloads data; Auto-load OFF updates address only

- [ ] 9. Implement range reading with chunking (50K rows/chunk for datasets > 100K rows) and type detection
  - **Requirements:** Req 3
  - **Design Reference:** §2.3 (Range Reading with Chunking)
  - **Files:** Modify `TaskPane/taskpane.js`
  - **Acceptance:** 100-row range loads in one pass; 150K-row range loads in 3 chunks; empty selection shows instruction; types detected correctly

- [ ] 10. Implement Export to Sheet function (create worksheet, write array at A1, auto-fit columns)
  - **Requirements:** Req 4
  - **Design Reference:** §2.3, Data Flow 2
  - **Files:** Modify `TaskPane/taskpane.js`
  - **Acceptance:** New worksheet created with timestamp name; data at A1; columns auto-fitted; >1M rows truncated with warning; confirmation toast shown

- [ ] 11. Implement apiCall fetch wrapper with timeout (10s), error display, and retry mechanism
  - **Requirements:** Req 6, Req 7, Req 8
  - **Design Reference:** §2.3 (Communication with HTTP Server)
  - **Files:** Modify `TaskPane/taskpane.js`
  - **Acceptance:** Successful call returns JSON; server down shows error + retry button; 10s timeout shows timeout message

### Phase 4: DuckDB API Endpoints

- [ ] 12. Initialize DuckDB in-memory connection and implement load_data() for table creation from received data
  - **Requirements:** Req 6, Req 13
  - **Design Reference:** §2.4 (DuckDB Integration — In-Memory Table)
  - **Files:** Modify `ControlPython/startup/neven_http_server.py`
  - **Acceptance:** POST data creates `dataset` table; second POST replaces it; types mapped correctly; DuckDB ≥0.9.0 verified

- [ ] 13. Implement POST /api/analyze endpoint with descriptive statistics (count, mean, std, min, quartiles, max)
  - **Requirements:** Req 6
  - **Design Reference:** §2.2 (Endpoints), §2.4, Data Flow 1
  - **Files:** Modify `ControlPython/startup/neven_http_server.py`
  - **Acceptance:** Returns correct statistics for known dataset; <5s for 1M rows; malformed request returns 400

- [ ] 14. Implement POST /api/groupby endpoint with metric validation and descending sort
  - **Requirements:** Req 7
  - **Design Reference:** §2.4 (GROUP BY Endpoint Logic), Data Flow 3
  - **Files:** Modify `ControlPython/startup/neven_http_server.py`
  - **Acceptance:** All 6 metrics work correctly; results sorted desc; invalid metric returns 400; <3s for 1M rows

- [ ] 15. Implement POST /api/query endpoint with 30s timeout, pagination (100 rows/page), and SELECT-only restriction
  - **Requirements:** Req 8
  - **Design Reference:** §2.4 (Query Execution with Timeout, Pagination)
  - **Files:** Modify `ControlPython/startup/neven_http_server.py`
  - **Acceptance:** Valid SQL returns paginated results; syntax error returns 400; timeout returns 408; DDL rejected; pagination navigates correctly

### Phase 5: Task Pane UI

- [ ] 16. Build Data Studio tab UI: Load Data button, preview table (20 rows), Analyze button, statistics results table
  - **Requirements:** Req 3, Req 6
  - **Design Reference:** §2.3 (Tab: Data Studio)
  - **Files:** Modify `TaskPane/taskpane.html`, Modify `TaskPane/taskpane.js`, Modify `TaskPane/taskpane.css`
  - **Acceptance:** Load Data shows preview; Analyze renders statistics table; loading spinner visible during fetch

- [ ] 17. Build GROUP BY controls (Group/Value/Metric dropdowns) with bar chart and results table rendering
  - **Requirements:** Req 7
  - **Design Reference:** §2.3 (Tab: Data Studio), Data Flow 3
  - **Files:** Modify `TaskPane/taskpane.html`, Modify `TaskPane/taskpane.js`, Modify `TaskPane/taskpane.css`
  - **Acceptance:** Dropdowns populated from loaded data types; chart + table render on selection; metric change updates in-place

- [ ] 18. Build SQL tab: query editor with highlighting, Ctrl+Enter execute, paginated results, error display, Export button
  - **Requirements:** Req 8
  - **Design Reference:** §2.3 (Tab: SQL), Data Flow 2
  - **Files:** Modify `TaskPane/taskpane.html`, Modify `TaskPane/taskpane.js`, Modify `TaskPane/taskpane.css`
  - **Acceptance:** Ctrl+Enter executes query; results paginated at 100/page; syntax error shown in red; Export writes to new worksheet

- [ ] 19. Build Viewers tab: navigation menu (5 viewer types) with iframe loading and dataset persistence across switches
  - **Requirements:** Req 11
  - **Design Reference:** §2.3 (Tab: Viewers), §5.3
  - **Files:** Modify `TaskPane/taskpane.html`, Modify `TaskPane/taskpane.js`, Modify `TaskPane/taskpane.css`
  - **Acceptance:** Each viewer loads its HTML via iframe; switching viewers does not re-fetch dataset; all 5 types load without errors

### Phase 6: Deployment + Integration

- [ ] 20. Add TaskPane config section to neven-config.json and conditional server startup in startup.py
  - **Requirements:** Req 12, Req 13
  - **Design Reference:** §2.6 (Configuration)
  - **Files:** Modify `DISTRIBUIR/NEVEN/Dist/neven-config.json`, Modify `ControlPython/startup/startup.py`
  - **Acceptance:** enabled=true starts server; enabled=false skips with log message; port/paths configurable

- [ ] 21. Add Phase 4b to Install-NEVEN.ps1: version check, cert generation, registry sideload, and Uninstall cleanup
  - **Requirements:** Req 10, Req 2
  - **Design Reference:** §2.5 (Deployment / Sideload)
  - **Files:** Modify `DISTRIBUIR/NEVEN/Install-NEVEN.ps1`, Modify `DISTRIBUIR/NEVEN/Uninstall-NEVEN.ps1`
  - **Acceptance:** Excel 16+ gets registry key + certs; Excel <16 aborts with message; Uninstall removes key + certs; restart shows add-in

- [ ] 22. Add NEVEN Studio button to CustomUI.xml and OnNEVENStudioCommand handler with WebView2 fallback
  - **Requirements:** Req 9, Req 12
  - **Design Reference:** §5.2 (COM Ribbon Button)
  - **Files:** Modify `Addin/CustomUI.xml`, Modify Ribbon source (NEVENRibbon handler)
  - **Acceptance:** Button opens Task Pane when enabled; opens WebView2 when disabled; existing Ribbon buttons unaffected

- [ ] 23. Integration testing: verify XLL/COM coexistence, WebView2 fallback, air-gapped operation, end-to-end flow
  - **Requirements:** Req 9, Req 12, Req 13
  - **Design Reference:** §Testing Strategy
  - **Files:** Create `tests/integration/test_taskpane_coexistence.py`, Create `TaskPane/README.md`
  - **Acceptance:** XLL functions work with Task Pane open; server down triggers WebView2 fallback; no internet needed; full flow Select→Load→Analyze→GroupBy→SQL→Export succeeds

## Task Dependency Graph

```json
{
  "waves": [
    {
      "tasks": [1, 5],
      "description": "HTTP server skeleton + manifest (no dependencies)"
    },
    {
      "tasks": [2, 6, 7],
      "description": "HTTPS + Task Pane shell + icons (depends on task 1, 5)",
      "dependsOn": [1, 5]
    },
    {
      "tasks": [3, 8],
      "description": "CORS/health endpoint + Office.js init (depends on task 2, 6)",
      "dependsOn": [2, 6]
    },
    {
      "tasks": [4, 9, 10, 11],
      "description": "Static serving + range reading + export + API client (depends on task 3, 8)",
      "dependsOn": [3, 8]
    },
    {
      "tasks": [12, 20],
      "description": "DuckDB connection + config section (depends on task 4)",
      "dependsOn": [4]
    },
    {
      "tasks": [13, 14, 15, 19],
      "description": "API endpoints (analyze, groupby, query) + viewers tab (depends on task 12, 4, 6)",
      "dependsOn": [12, 4, 6]
    },
    {
      "tasks": [16, 17, 18],
      "description": "Task Pane UI tabs: Data Studio + GROUP BY + SQL (depends on task 11, 13, 14, 15)",
      "dependsOn": [11, 13, 14, 15]
    },
    {
      "tasks": [21, 22],
      "description": "Install script + Ribbon button (depends on task 5, 20)",
      "dependsOn": [5, 20]
    },
    {
      "tasks": [23],
      "description": "Integration testing (depends on all previous tasks)",
      "dependsOn": [16, 17, 18, 19, 21, 22]
    }
  ]
}
```

## Notes

<!-- Notas para el equipo NEVEN -->

- Las tareas 1-4 son puramente Python y no requieren compilación C++.
- Las tareas 5-7 son archivos estáticos que se pueden crear en paralelo con la Fase 1.
- La Fase 3 (Office.js) solo se puede probar completamente dentro de Excel con el manifest sideloaded.
- DuckDB (Fase 4) se puede probar independientemente con pytest antes de integrar con el frontend.
- La Fase 6 modifica scripts de instalación existentes — hacer backup antes de editar.
- El certificado autofirmado requiere que el usuario lo acepte en el navegador la primera vez (o lo agregue al trusted store durante instalación).
