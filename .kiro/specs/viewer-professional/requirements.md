# Requirements Document

## Introduction

This feature professionalizes the NEVEN WebView2 Viewer with three capabilities: (1) automatic content refresh when Excel data changes, (2) a floating Save button for exporting visualizations as HTML/PNG/PDF, and (3) document viewing support for PDF, TXT, DOCX, and DOC files. These improvements transform the viewer from a basic HTML display into a production-ready visualization and document tool suitable for professional presentations and workflows.

## Glossary

- **Viewer**: The Win32 modeless window hosting a WebView2 controller, managed by `ViewerManager` singleton.
- **ViewerWindow**: The C++ class (`rj2xcl::ViewerWindow`) that wraps a Win32 HWND + ICoreWebView2Controller.
- **ContentPipeline**: The routing layer that determines how content (HTML, Markdown, file paths) reaches the viewer.
- **RJ_View**: The `=NEVEN.v()` UDF entry point that creates or reuses a viewer window.
- **PostMessageBridge**: The JS↔C++ communication layer using `window.chrome.webview.postMessage`.
- **STA_Thread**: The dedicated Single-Threaded Apartment thread where all WebView2 COM operations execute.
- **Auto_Refresh**: The mechanism by which the viewer updates its displayed content when the underlying Excel data changes and the UDF recalculates.
- **Save_Dialog**: The native Windows file save dialog invoked via `GetSaveFileName` API.
- **Pandoc**: The document conversion tool (available via Quarto installation) used to convert DOCX/DOC to HTML.
- **Plotly_Export**: The `Plotly.downloadImage()` JavaScript API for exporting Plotly charts as PNG/SVG/PDF.

## Requirements

### Requirement 1: Auto-Refresh on UDF Recalculation

**User Story:** As an Excel user, I want the viewer to automatically update when I change values in the range that feeds a visualization, so that I can see live results without closing and reopening the viewer.

#### Acceptance Criteria

1. WHEN the `RJ_View` UDF recalculates with new content, THE Viewer SHALL navigate to the updated content within the existing viewer window without creating a new window.
2. WHILE the Viewer is displaying content and a refresh occurs, THE Viewer SHALL preserve the current scroll position after navigation completes.
3. WHILE the Viewer is displaying content and a refresh occurs, THE Viewer SHALL avoid visible flickering by completing the navigation before showing the new content.
4. WHEN the `RJ_View` UDF recalculates with content identical to the currently displayed content, THE Viewer SHALL skip the navigation to avoid unnecessary reloads.
5. IF the viewer window has been closed by the user before a recalculation, THEN THE RJ_View UDF SHALL create a new viewer window with the updated content.

### Requirement 2: Floating Save Button

**User Story:** As a professional user, I want a Save button in the viewer that lets me export the current visualization as HTML, PNG, or PDF, so that I can include it in presentations and reports.

#### Acceptance Criteria

1. THE Viewer SHALL display a floating Save button in the bottom-right corner of the viewer window.
2. THE Save_Button SHALL render as a semi-transparent icon that becomes fully opaque on mouse hover.
3. WHEN the user clicks the Save button, THE Viewer SHALL open a native Windows Save_Dialog using the `GetSaveFileName` API.
4. THE Save_Dialog SHALL offer file type filters for HTML (.html), PNG (.png), and PDF (.pdf) formats.
5. WHEN the user selects HTML format in the Save_Dialog, THE Viewer SHALL save the complete current page source as a self-contained HTML file.
6. WHEN the user selects PNG format and the page contains a Plotly chart, THE Viewer SHALL invoke `Plotly.downloadImage()` to generate the PNG at the specified path.
7. WHEN the user selects PDF format and the page contains a Plotly chart, THE Viewer SHALL invoke `Plotly.downloadImage()` with format "pdf" to generate the PDF at the specified path.
8. WHEN the user selects PNG format and the page does not contain a Plotly chart, THE Viewer SHALL capture the full page as a PNG using the WebView2 `CapturePreview` API.
9. WHEN the user selects PDF format and the page does not contain a Plotly chart, THE Viewer SHALL print the page to PDF using the WebView2 `PrintToPdf` API.
10. IF the save operation fails due to file system permissions or disk space, THEN THE Viewer SHALL display an error notification to the user via the PostMessageBridge notify mechanism.
11. WHILE the save operation is in progress, THE Save_Button SHALL display a brief progress indicator to confirm the action was initiated.

### Requirement 3: PDF Document Viewing

**User Story:** As a user, I want to view PDF files directly in the NEVEN viewer by passing a PDF path to `=NEVEN.v()`, so that I can reference documents alongside my Excel data.

#### Acceptance Criteria

1. WHEN the `RJ_View` UDF receives a file path ending in `.pdf` (case-insensitive), THE ContentPipeline SHALL route the file to the viewer using WebView2 native PDF rendering via `file:///` navigation.
2. THE Viewer SHALL display the PDF with WebView2's built-in PDF controls (zoom, page navigation, search).
3. IF the PDF file does not exist at the specified path, THEN THE RJ_View UDF SHALL return a descriptive error string indicating the file was not found.

### Requirement 4: TXT Document Viewing

**User Story:** As a user, I want to view plain text files in the NEVEN viewer by passing a TXT path to `=NEVEN.v()`, so that I can display text content in a readable format.

#### Acceptance Criteria

1. WHEN the `RJ_View` UDF receives a file path ending in `.txt` (case-insensitive), THE ContentPipeline SHALL read the file content and wrap it in a styled HTML page with monospace font and dark theme.
2. THE Viewer SHALL display the text content preserving whitespace and line breaks.
3. IF the TXT file does not exist at the specified path, THEN THE RJ_View UDF SHALL return a descriptive error string indicating the file was not found.

### Requirement 5: DOCX Document Viewing

**User Story:** As a user, I want to view Word documents (.docx) in the NEVEN viewer by passing a DOCX path to `=NEVEN.v()`, so that I can preview documents without opening Microsoft Word.

#### Acceptance Criteria

1. WHEN the `RJ_View` UDF receives a file path ending in `.docx` (case-insensitive), THE ContentPipeline SHALL convert the file to HTML using Pandoc and display the result in the viewer.
2. THE ContentPipeline SHALL invoke Pandoc as a child process with arguments `--from=docx --to=html --standalone` to produce a self-contained HTML file.
3. THE ContentPipeline SHALL locate Pandoc by checking the system PATH first, then falling back to `C:\Quarto\bin\pandoc.exe`.
4. IF Pandoc is not found at any expected location, THEN THE RJ_View UDF SHALL return a descriptive error string indicating that Pandoc is required for DOCX viewing.
5. IF Pandoc conversion fails with a non-zero exit code, THEN THE RJ_View UDF SHALL return a descriptive error string including the Pandoc stderr output.
6. WHEN the conversion succeeds, THE Viewer SHALL display the resulting HTML with proper formatting of headings, paragraphs, tables, and images.

### Requirement 6: DOC Document Viewing

**User Story:** As a user, I want to view legacy Word documents (.doc) in the NEVEN viewer by passing a DOC path to `=NEVEN.v()`, so that I can preview older documents without opening Microsoft Word.

#### Acceptance Criteria

1. WHEN the `RJ_View` UDF receives a file path ending in `.doc` (case-insensitive), THE ContentPipeline SHALL convert the file to HTML using Pandoc and display the result in the viewer.
2. THE ContentPipeline SHALL invoke Pandoc as a child process with arguments `--from=doc --to=html --standalone` to produce a self-contained HTML file.
3. IF Pandoc is not found, THEN THE RJ_View UDF SHALL return a descriptive error string indicating that Pandoc is required for DOC viewing.
4. IF Pandoc conversion fails with a non-zero exit code, THEN THE RJ_View UDF SHALL return a descriptive error string including the Pandoc stderr output.

### Requirement 7: Backward Compatibility

**User Story:** As an existing NEVEN user, I want all current `=NEVEN.v()` usage patterns to continue working unchanged, so that my existing workbooks are not broken by the new features.

#### Acceptance Criteria

1. THE RJ_View UDF SHALL continue to accept inline HTML strings and display them in the viewer.
2. THE RJ_View UDF SHALL continue to accept `.html` and `.htm` file paths and display them in the viewer.
3. THE RJ_View UDF SHALL continue to accept Markdown content and render it with the marked.js wrapper.
4. THE RJ_View UDF SHALL continue to reuse the last viewer window when the viewer is still alive.
5. THE Save_Button SHALL not interfere with existing PostMessageBridge communication or Plotly chart interactivity.
6. THE Viewer SHALL not alter the existing snap-to-right-half layout behavior.
