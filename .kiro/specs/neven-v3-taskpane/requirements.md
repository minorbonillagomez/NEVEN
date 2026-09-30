# Requirements Document

## Introduction

NEVEN v3.0 Task Pane embeds the NEVEN Viewer as an Excel Task Pane (side panel) using the Office.js API, enabling bidirectional communication between the HTML panel and Excel cells. This eliminates the need for intermediate formulas (`=P.*`, `=NEVEN.v()`) for interactive data analysis, allowing users to select ranges, run DuckDB-powered queries, and export results directly from the panel. The feature coexists with the existing XLL add-in (NEVEN64.xll) and COM Ribbon (NEVENRibbon.dll) on the same machine.

## Glossary

- **Task_Pane**: An Excel side panel rendered via Office.js that hosts HTML/JavaScript content within the Excel window
- **Office_JS**: Microsoft's JavaScript API for interacting with Excel workbooks, worksheets, and ranges from a Task Pane
- **ControlPython**: The child process (ControlPython.exe) that embeds Python via Stable ABI and communicates with NEVEN64.xll through Named Pipes
- **HTTP_Server**: A local HTTP server running on localhost:5555 inside ControlPython.exe that serves Task Pane HTML and handles API requests
- **DuckDB**: An in-process analytical SQL engine used for fast aggregation and query execution on large datasets
- **Manifest**: An XML file (manifest.xml) conforming to the Office Add-in schema that registers the Task Pane with Excel
- **Sideload**: A deployment method for Office Add-ins that does not require AppSource publication — uses shared folders or Windows registry entries
- **Data_Studio**: The interactive analysis view within the Task Pane where users select data ranges, trigger analyses, and view results
- **XLL**: The native Excel add-in binary (NEVEN64.xll) that exposes worksheet functions via the Excel C API
- **COM_Ribbon**: The NEVENRibbon.dll component that provides the NEVEN tab in the Excel ribbon
- **EquivalentAddins**: An XML element in the Office Add-in manifest that declares coexistence with XLL/COM add-ins
- **PostMessage_Bridge**: An optional communication channel between the XLL and the Task Pane using window messages
- **Selected_Range**: The currently selected cell range in the active Excel worksheet, accessible via Office.js API

## Requirements

### Requirement 1: Office Web Add-in Manifest

**User Story:** As a developer, I want a valid Office Web Add-in manifest file, so that Excel registers and loads the NEVEN Task Pane on startup or via ribbon button.

#### Acceptance Criteria

1. THE Manifest SHALL conform to the Office Add-in XML schema version 1.1 (TaskPaneApp type)
2. THE Manifest SHALL specify `https://localhost:5555/taskpane.html` as the default SourceLocation
3. THE Manifest SHALL declare the Host as "Workbook" to restrict loading to Excel
4. THE Manifest SHALL request ReadWriteDocument permissions to enable reading and writing cell data
5. THE Manifest SHALL include an EquivalentAddins element declaring NEVEN64.xll (type XLL) for coexistence
6. THE Manifest SHALL set DefaultLocale to "es-ES" and DisplayName to "NEVEN Studio"
7. WHEN Excel loads the Manifest, THE Task_Pane SHALL appear as an available add-in in Excel's insert panel

### Requirement 2: HTTP Server in ControlPython

**User Story:** As the Task Pane front-end, I want a local HTTP server in ControlPython.exe, so that HTML assets and API endpoints are accessible from localhost:5555.

#### Acceptance Criteria

1. WHEN ControlPython.exe starts, THE HTTP_Server SHALL bind to localhost port 5555 and begin accepting HTTP requests
2. THE HTTP_Server SHALL serve static files (HTML, CSS, JavaScript) from a configurable directory for Task Pane assets
3. THE HTTP_Server SHALL expose a `/health` endpoint that returns HTTP 200 with a JSON status object
4. THE HTTP_Server SHALL include CORS headers (`Access-Control-Allow-Origin: https://localhost:5555`) in all responses to permit Office.js fetch requests
5. THE HTTP_Server SHALL run on a dedicated thread separate from the Named Pipe loop to avoid blocking IPC communication
6. IF the HTTP_Server fails to bind to port 5555, THEN THE HTTP_Server SHALL log the error and retry on port 5556 as fallback
7. THE HTTP_Server SHALL use HTTPS with a self-signed localhost certificate to satisfy Office.js security requirements

### Requirement 3: Office.js Range Reading

**User Story:** As a user, I want the Task Pane to read the currently selected Excel range, so that I can analyze data without copying it manually.

#### Acceptance Criteria

1. WHEN the user clicks "Load Data" in the Task_Pane, THE Office_JS integration SHALL read the values, address, column count, and row count of the Selected_Range
2. WHEN the Selected_Range contains more than 100,000 rows, THE Office_JS integration SHALL read data in chunks of 50,000 rows to avoid memory limits
3. THE Office_JS integration SHALL detect column data types (numeric, text, date) from the first 100 rows of the Selected_Range
4. IF the Selected_Range is empty, THEN THE Task_Pane SHALL display a message instructing the user to select a data range
5. WHEN data is loaded, THE Task_Pane SHALL display a preview table showing the first 20 rows and all detected columns

### Requirement 4: Write Results to Excel

**User Story:** As a user, I want to export analysis results from the Task Pane back into Excel worksheets, so that I can use the output in further spreadsheet work.

#### Acceptance Criteria

1. WHEN the user clicks "Export to Sheet" in the Task_Pane, THE Office_JS integration SHALL create a new worksheet with a name based on the analysis type and timestamp
2. THE Office_JS integration SHALL write the result data as a two-dimensional array starting at cell A1 of the new worksheet
3. WHEN results are written, THE Office_JS integration SHALL apply auto-fit to all columns containing data
4. IF the result dataset exceeds 1,048,576 rows (Excel row limit), THEN THE Task_Pane SHALL truncate the output and display a warning indicating the number of rows omitted
5. WHEN the export completes successfully, THE Task_Pane SHALL display a confirmation message with the target worksheet name

### Requirement 5: Selection Change Reactivity

**User Story:** As a user, I want the Task Pane to react when I select a different range in Excel, so that the panel always shows context for my current selection.

#### Acceptance Criteria

1. WHEN the user changes the selected range in Excel, THE Office_JS integration SHALL fire an event handler within 200 milliseconds
2. WHEN a selection change event fires, THE Task_Pane SHALL update the status bar showing the new range address and dimensions
3. WHILE the "Auto-load" toggle is enabled, THE Task_Pane SHALL automatically reload data from the new Selected_Range on each selection change
4. WHILE the "Auto-load" toggle is disabled, THE Task_Pane SHALL update only the address display without reloading data

### Requirement 6: Data Studio Analysis

**User Story:** As a user, I want to send my selected data to DuckDB for analysis, so that I get instant statistical summaries and visualizations in the panel.

#### Acceptance Criteria

1. WHEN the user clicks "Analyze" in the Data_Studio, THE Task_Pane SHALL send the loaded data to the HTTP_Server endpoint `/api/analyze` via POST request
2. THE HTTP_Server SHALL load the received data into a DuckDB in-memory table and compute descriptive statistics (count, mean, standard deviation, min, max, quartiles) for each numeric column
3. WHEN analysis completes, THE Task_Pane SHALL render results as a formatted table with one row per column and statistics as sub-columns
4. THE HTTP_Server SHALL complete the analysis and return results within 5 seconds for datasets up to 1,000,000 rows
5. IF the `/api/analyze` request fails, THEN THE Task_Pane SHALL display the error message returned by the HTTP_Server and offer a retry button

### Requirement 7: Live GROUP BY Aggregation

**User Story:** As a user, I want to perform GROUP BY aggregations via dropdown controls in the Task Pane, so that I can explore aggregated views of my data without writing formulas.

#### Acceptance Criteria

1. WHEN data is loaded, THE Data_Studio SHALL populate a "Group Column" dropdown with all detected categorical (text) columns
2. WHEN data is loaded, THE Data_Studio SHALL populate a "Value Column" dropdown with all detected numeric columns
3. THE Data_Studio SHALL provide a "Metric" dropdown with options: SUM, AVG, COUNT, MIN, MAX, MEDIAN
4. WHEN the user selects a group column, value column, and metric, THE Task_Pane SHALL send a POST request to `/api/groupby` with the selected parameters
5. THE HTTP_Server SHALL execute the GROUP BY query via DuckDB on the full dataset and return results sorted by the metric value in descending order
6. WHEN results return, THE Task_Pane SHALL render a bar chart and a results table showing each group and its aggregated value
7. THE HTTP_Server SHALL complete GROUP BY queries within 3 seconds for datasets up to 1,000,000 rows

### Requirement 8: SQL Query Builder

**User Story:** As a user, I want to type and execute SQL queries against my loaded data in the Task Pane, so that I can perform custom analyses without leaving Excel.

#### Acceptance Criteria

1. THE Data_Studio SHALL provide a text area for SQL input with syntax highlighting for SQL keywords
2. WHEN the user clicks "Execute" or presses Ctrl+Enter, THE Task_Pane SHALL send the SQL text to the HTTP_Server endpoint `/api/query` via POST request
3. THE HTTP_Server SHALL execute the SQL query against the currently loaded DuckDB table and return results as a JSON array of row objects
4. WHEN query results return, THE Task_Pane SHALL render them as a scrollable table with column headers
5. IF the SQL query contains a syntax error, THEN THE HTTP_Server SHALL return HTTP 400 with the DuckDB error message, and THE Task_Pane SHALL display the error below the SQL input
6. THE HTTP_Server SHALL impose a query timeout of 30 seconds and return HTTP 408 if exceeded
7. WHEN the query returns more than 10,000 rows, THE Task_Pane SHALL paginate results showing 100 rows per page with navigation controls

### Requirement 9: Coexistence with XLL and COM Ribbon

**User Story:** As a user, I want the Task Pane to work alongside the existing NEVEN64.xll and NEVENRibbon.dll, so that all worksheet functions and ribbon buttons remain functional.

#### Acceptance Criteria

1. WHILE the Task_Pane is loaded, THE XLL SHALL continue to register and execute all worksheet functions (=P.*, =R.*, =J.*)
2. WHILE the Task_Pane is loaded, THE COM_Ribbon SHALL continue to display the NEVEN tab and respond to button clicks
3. THE Manifest SHALL declare EquivalentAddins with FileName "NEVEN64.xll" and Type "XLL" to prevent Excel from disabling the XLL
4. WHEN Excel loads both the Task_Pane add-in and the XLL, THE system SHALL not produce duplicate function registrations or namespace conflicts
5. IF the Task_Pane fails to load (HTTP_Server unavailable), THEN THE XLL and COM_Ribbon SHALL continue to operate without degradation

### Requirement 10: Sideload Deployment

**User Story:** As an administrator, I want to deploy the Task Pane via sideload (shared folder or registry), so that installation does not require AppSource publication or internet access.

#### Acceptance Criteria

1. THE installation script SHALL support shared-folder sideload by copying manifest.xml to a network share and configuring the Excel trusted catalog path
2. THE installation script SHALL support registry-based sideload by writing the manifest path to `HKCU\Software\Microsoft\Office\16.0\WEF\Developer\` registry key
3. WHEN the sideload is configured, THE Task_Pane SHALL appear in Excel within one restart of the application
4. THE installation script SHALL verify that the target Excel version is 2016 or later (build 16.0+) before proceeding
5. IF the target Excel version is below 2016, THEN THE installation script SHALL abort with a message indicating the minimum supported version

### Requirement 11: Existing Viewers in Task Pane

**User Story:** As a user, I want to access all existing NEVEN viewers (Dashboard, Geodata, Timeline, Network, ML Reports) from the Task Pane, so that I have a unified interface for all visualizations.

#### Acceptance Criteria

1. THE Task_Pane SHALL provide a navigation menu listing all available viewer types: Dashboard, Geodata, Timeline, Network, and ML Reports
2. WHEN the user selects a viewer type from the navigation menu, THE Task_Pane SHALL load the corresponding HTML viewer within the panel iframe or container
3. THE HTTP_Server SHALL serve all existing viewer HTML assets from the same static directory used by the WebView2 popup viewers
4. WHILE a viewer is active in the Task_Pane, THE viewer SHALL receive data from the HTTP_Server using the same API endpoints as the Data_Studio
5. WHEN the user switches between viewer types, THE Task_Pane SHALL preserve the currently loaded dataset in memory to avoid redundant reloads

### Requirement 12: Fallback to v2.1 WebView2 Viewer

**User Story:** As a user, I want the existing WebView2 popup viewers to remain functional as a fallback, so that I can still use NEVEN visualizations if the Task Pane is unavailable.

#### Acceptance Criteria

1. WHILE Office.js is unavailable (Excel version below 2016), THE system SHALL use the existing WebView2 popup viewer for all visualization requests
2. WHEN the HTTP_Server is unreachable, THE XLL SHALL fall back to the existing WebView2 viewer mechanism using local file paths
3. THE neven-config.json SHALL include a `TaskPane.enabled` boolean field that allows administrators to disable the Task Pane and force WebView2 fallback
4. WHEN `TaskPane.enabled` is set to false, THE COM_Ribbon button SHALL open the WebView2 popup viewer instead of the Task Pane

### Requirement 13: Platform and Version Constraints

**User Story:** As a developer, I want clear platform constraints documented, so that the implementation targets the correct Windows and Excel versions.

#### Acceptance Criteria

1. THE Task_Pane feature SHALL target Windows 10 (build 1903+) and Windows 11 as supported operating systems
2. THE Task_Pane feature SHALL require Excel 2016 (build 16.0.4266+) or Microsoft 365 as the minimum Excel version
3. THE HTTP_Server SHALL require Python 3.10 or later (consistent with ControlPython Stable ABI requirements)
4. THE HTTP_Server SHALL require DuckDB 0.9.0 or later as the SQL engine dependency
5. THE Task_Pane SHALL function without internet connectivity by serving all assets from localhost

