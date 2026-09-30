# Implementation Plan: Viewer Professional

## Overview

This plan implements three professional capabilities for the NEVEN WebView2 Viewer: auto-refresh with content hashing and scroll preservation, a floating save button with HTML/PNG/PDF export, and document viewing for PDF/TXT/DOCX/DOC files. Implementation proceeds incrementally: content detection first, then document conversion, then viewer extensions, then save functionality, and finally the updated UDF routing logic.

## Tasks

- [x] 1. Extend ContentPipeline with document type detection and content hashing
  - [x] 1.1 Add file extension detection methods to ContentPipeline
    - Add `IsPdfFile`, `IsTxtFile`, `IsDocxFile`, `IsDocFile`, `IsDocumentFile` static methods to `ContentPipeline.h`
    - Implement in `ContentPipeline.cc` with case-insensitive extension matching
    - `IsDocFile` must return false for `.docx` paths (check that extension is exactly `.doc`)
    - _Requirements: 3.1, 4.1, 5.1, 6.1_

  - [x] 1.2 Add ComputeContentHash to ContentPipeline
    - Add `static size_t ComputeContentHash(const std::string& content)` to header and implementation
    - Use `std::hash<std::string>` for fast hashing
    - _Requirements: 1.4_

  - [x] 1.3 Write unit tests for file extension detection and content hashing
    - Create `NEVEN/tests/viewer_professional_tests.cc`
    - Test each detector with representative paths (`.pdf`, `.PDF`, `.txt`, `.docx`, `.doc`, `.html`)
    - Test mutual exclusivity: only one detector returns true per path
    - Test `ComputeContentHash` determinism: same input → same output
    - Test that different inputs produce different hashes (representative cases)
    - Add the new test file to `NEVEN/tests/CMakeLists.txt`
    - _Requirements: 3.1, 4.1, 5.1, 6.1, 1.4_

  - [ ]* 1.4 Write property test for file extension classification (Property 1)
    - **Property 1: File extension classification is correct and mutually exclusive**
    - Generate random file paths with extensions from {.pdf, .txt, .docx, .doc, .html, .htm, .css, .js, .png, ""} with random case variations
    - Verify mutual exclusivity: at most one document-type detector returns true
    - Verify correct classification based on extension
    - Add to `NEVEN/tests/viewer_professional_pbt.cc`
    - **Validates: Requirements 3.1, 4.1, 5.1, 6.1**

  - [ ]* 1.5 Write property test for content hash determinism (Property 2)
    - **Property 2: Content hash is deterministic (identical content → identical hash)**
    - Generate random strings (length 0–10000, random bytes)
    - Verify `ComputeContentHash(s) == ComputeContentHash(s)` always holds
    - Add to `NEVEN/tests/viewer_professional_pbt.cc`
    - **Validates: Requirements 1.4**

- [x] 2. Implement TXT document viewing
  - [x] 2.1 Implement WrapTxtAsHtml in ContentPipeline
    - Add `static std::string WrapTxtAsHtml(const std::string& file_path)` to header
    - Read file content, HTML-escape special characters (`<`, `>`, `&`, `"`)
    - Wrap in dark-theme HTML with `<pre>` element, monospace font, `background:#1e1e1e`
    - Return empty string if file cannot be opened
    - _Requirements: 4.1, 4.2, 4.3_

  - [x] 2.2 Write unit tests for WrapTxtAsHtml
    - Test with a temp file containing known text content
    - Verify output contains `<pre>` with the original text (HTML-escaped)
    - Verify dark theme CSS is present
    - Verify special characters are properly escaped
    - Verify empty string returned for non-existent file
    - _Requirements: 4.1, 4.2, 4.3_

  - [ ]* 2.3 Write property test for TXT wrapping (Property 3)
    - **Property 3: TXT wrapping preserves original text content**
    - Generate random text strings (including special chars, unicode, empty lines)
    - Write to temp file, call `WrapTxtAsHtml`, verify HTML-escaped text appears in output
    - Verify output has valid HTML structure (doctype, html, body, pre elements)
    - Add to `NEVEN/tests/viewer_professional_pbt.cc`
    - **Validates: Requirements 4.1, 4.2**

- [x] 3. Implement Pandoc-based document conversion (DOCX/DOC)
  - [x] 3.1 Implement FindPandoc in ContentPipeline
    - Add `static std::string FindPandoc()` to header and implementation
    - Search system PATH first using `SearchPathA` or iterating PATH entries
    - Fall back to `C:\Quarto\bin\pandoc.exe` if not in PATH
    - Return full path or empty string if not found
    - _Requirements: 5.3, 6.3_

  - [x] 3.2 Implement ConvertWithPandoc in ContentPipeline
    - Add `static std::string ConvertWithPandoc(const std::string& file_path, const std::string& from_format)` to header
    - Call `FindPandoc()` first; return error string if not found
    - Check file exists with `GetFileAttributesA`; return error if not found
    - Use `CreateProcess` with `--from={format} --to=html --standalone` arguments
    - Redirect stdout and stderr via pipes (`STARTUPINFO` with `hStdOutput`/`hStdError`)
    - Use `WaitForSingleObject` with 30-second timeout
    - On timeout: `TerminateProcess` and return `"Error: Pandoc timed out (30s)"`
    - On non-zero exit: return `"Error: Pandoc conversion failed — {stderr}"`
    - On success: return the stdout HTML content
    - _Requirements: 5.1, 5.2, 5.4, 5.5, 6.1, 6.2, 6.3, 6.4_

  - [x] 3.3 Write unit tests for Pandoc conversion logic
    - Test `FindPandoc` returns empty when pandoc is not available (mock scenario)
    - Test `ConvertWithPandoc` error string when file doesn't exist
    - Test `ConvertWithPandoc` error string when Pandoc not found
    - Test error message format includes stderr content
    - _Requirements: 5.4, 5.5, 6.3, 6.4_

- [x] 4. Checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Extend ViewerWindow with save operations and scroll preservation
  - [x] 5.1 Add content hash and scroll state members to ViewerWindow
    - Add `size_t content_hash_` member (initialized to 0)
    - Add `int saved_scroll_x_` and `int saved_scroll_y_` members (initialized to 0)
    - Add `GetContentHash()`, `SetContentHash(size_t)` accessors
    - _Requirements: 1.2, 1.4_

  - [x] 5.2 Implement SaveScrollPosition and RestoreScrollPosition
    - `SaveScrollPosition()`: execute JS `window.scrollX/Y` via `ExecuteScript`, store results
    - `RestoreScrollPosition()`: execute JS `window.scrollTo(x, y)` after navigation completes
    - Register `NavigationCompleted` event handler to trigger restore
    - _Requirements: 1.2_

  - [x] 5.3 Implement GetPageSource method
    - Execute `document.documentElement.outerHTML` via `ExecuteScript`
    - Parse the JSON-encoded result string and pass to callback
    - _Requirements: 2.5_

  - [x] 5.4 Implement CaptureAsPng method
    - Use `ICoreWebView2::CapturePreview` with `COREWEBVIEW2_CAPTURE_PREVIEW_IMAGE_FORMAT_PNG`
    - Create output stream via `SHCreateStreamOnFileEx`
    - Call callback with HRESULT on completion
    - _Requirements: 2.8_

  - [x] 5.5 Implement PrintToPdf method
    - Query `ICoreWebView2_7` interface from webview
    - Call `PrintToPdf` with default print settings
    - Call callback with HRESULT on completion
    - _Requirements: 2.9_

  - [x] 5.6 Implement ExportPlotly method
    - Execute JS to check `window.Plotly` existence
    - If Plotly present: call `Plotly.downloadImage` with format and filename
    - Call callback with success/failure
    - _Requirements: 2.6, 2.7_

- [x] 6. Implement Save Button injection and PostMessageBridge handler
  - [x] 6.1 Inject Save Button script via AddScriptToExecuteOnDocumentCreated
    - Add the save button JavaScript (from design §5) as a second injected script in `ViewerWindow::InjectBridgeScript()`
    - Button: fixed position bottom-right, semi-transparent, opaque on hover
    - On click: send `{ action: "save-request" }` via `postMessage`, show ⏳ indicator for 2s
    - _Requirements: 2.1, 2.2, 2.11_

  - [x] 6.2 Add "save-request" action handler to PostMessageBridge
    - In `PostMessageBridge::OnWebMessageReceived`, add `else if (action == "save-request")` branch
    - Call `GetSaveFileName` on the STA thread with HTML/PNG/PDF filter spec
    - Based on selected filter index, dispatch to appropriate save method on the ViewerWindow
    - For HTML: call `GetPageSource` → write to file
    - For PNG: check Plotly first → `ExportPlotly` or `CaptureAsPng`
    - For PDF: check Plotly first → `ExportPlotly` or `PrintToPdf`
    - On failure: send notify message via PostMessageBridge
    - _Requirements: 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 2.10_

  - [x] 6.3 Write unit tests for PostMessageBridge save-request routing
    - Test that "save-request" action is recognized and does not produce "unrecognized action" warning
    - Test that existing "write-cell" and "notify" actions still work unchanged
    - Test save filter string contains all three formats
    - _Requirements: 2.3, 7.5_

- [x] 7. Checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Update RJ_View UDF with auto-refresh, content hash, and document routing
  - [x] 8.1 Add content hash comparison to RJ_View reuse logic
    - Before navigating an existing viewer, compute `ContentPipeline::ComputeContentHash(content)`
    - Compare with `viewer_window->GetContentHash()`
    - If hashes match: skip navigation, return existing viewer_id immediately
    - If hashes differ: proceed with navigation and update stored hash
    - _Requirements: 1.1, 1.4_

  - [x] 8.2 Add scroll preservation to RJ_View navigation path
    - Before navigating to new content: call `SaveScrollPosition()` on the viewer
    - After navigation completes: `RestoreScrollPosition()` is triggered by NavigationCompleted handler
    - _Requirements: 1.2_

  - [x] 8.3 Add document type routing to RJ_View UDF
    - After existing HTML/Markdown checks, add detection for document types:
    - `IsPdfFile` → verify file exists → `CreateViewerFromFile` (WebView2 native PDF rendering)
    - `IsTxtFile` → verify file exists → `WrapTxtAsHtml` → `CreateViewer` with HTML
    - `IsDocxFile` → verify file exists → `ConvertWithPandoc("docx")` → `CreateViewer` with HTML
    - `IsDocFile` → verify file exists → `ConvertWithPandoc("doc")` → `CreateViewer` with HTML
    - Return descriptive error string if file not found
    - Return Pandoc error string if conversion fails
    - _Requirements: 3.1, 3.2, 3.3, 4.1, 4.2, 4.3, 5.1, 5.2, 5.5, 5.6, 6.1, 6.4_

  - [x] 8.4 Ensure viewer-closed detection creates new window
    - Use existing `IsViewerAlive` check before attempting reuse
    - If viewer was closed by user: create new viewer with updated content (existing behavior, verify preserved)
    - _Requirements: 1.5_

  - [x] 8.5 Write unit tests for RJ_View document routing logic
    - Test PDF path detection routes to file-based viewer creation
    - Test TXT path detection routes through WrapTxtAsHtml
    - Test DOCX/DOC path detection routes through ConvertWithPandoc
    - Test file-not-found returns descriptive error string
    - Test backward compatibility: inline HTML, .html files, Markdown all still work
    - _Requirements: 3.3, 4.3, 5.5, 6.4, 7.1, 7.2, 7.3, 7.4_

- [x] 9. Add ViewerEntry extensions for hash and scroll state in ViewerManager
  - [x] 9.1 Extend ViewerEntry struct with content_hash and scroll fields
    - Add `size_t content_hash = 0` to `ViewerEntry` in `ViewerManager.h`
    - Add `int scroll_x = 0` and `int scroll_y = 0` to `ViewerEntry`
    - Update `NavigateViewerToString` and `NavigateViewerToFile` to accept/update hash
    - _Requirements: 1.2, 1.4_

  - [x] 9.2 Add WM_APP_SAVE_CONTENT message handling to STA thread
    - Define `WM_APP_SAVE_CONTENT = WM_APP + 105` and `SaveContentRequest` struct
    - Handle in the STA message pump: locate viewer, dispatch save based on format
    - _Requirements: 2.3_

- [x] 10. Final integration and backward compatibility verification
  - [x] 10.1 Wire all components together in the build system
    - Ensure `ContentPipeline.cc` compiles with new methods (no new source files needed for Common.lib)
    - Ensure `ViewerWindow.cc` compiles with new methods
    - Ensure `PostMessageBridge.cc` compiles with new action handler
    - Verify no linker errors with updated `basic_functions.cc`
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_

  - [ ]* 10.2 Write integration tests for auto-refresh flow
    - Test same content → no navigation call (mock ViewerManager)
    - Test different content → navigation called with scroll save/restore
    - Test viewer closed → new viewer created
    - _Requirements: 1.1, 1.2, 1.4, 1.5_

  - [ ]* 10.3 Write integration tests for save flow
    - Test HTML save dispatches ExecuteScript for outerHTML
    - Test PNG save (no Plotly) dispatches CapturePreview
    - Test PDF save (no Plotly) dispatches PrintToPdf
    - Test PNG/PDF save (with Plotly) dispatches Plotly.downloadImage
    - _Requirements: 2.5, 2.6, 2.7, 2.8, 2.9_

- [x] 11. Final checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- All tests run without Excel, WebView2, or Pandoc via mocks (per project convention)
- The project uses GTest v1.14.0 with a custom property test harness (`std::mt19937` + 100 iterations)
- C++17, MSVC 2022, CMake build system
