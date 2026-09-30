# Implementation Plan: Quarto Integration (RJ2XCL.Q)

## Overview

Adds a stateless `RJ2XCL.Q` worksheet function that renders Quarto `.qmd` documents from Excel cells. The implementation is isolated in two new files (`QuartoService.h` + `QuartoService.cc`) with minimal touchpoints to existing code: one new export in `basic_functions`, one `funcTemplates` entry, new ConfigService getters, one initialization line in `rj2xcl.cc`, and a config file update. Tasks are ordered so that each step compiles and passes the existing test suite before the next begins.

## Tasks

- [x] 1. Add Quarto configuration support
  - [x] 1.1 Add `Quarto` section to `rj2xcl-config.json`
    - Add the `Quarto` key to `RJ2XCL/Install/rj2xcl-config.json` with: `enabled` (true), `path` (""), `outputDirectory` ("%USERPROFILE%\\Documents\\RJ2XCL\\reports"), `defaultFormat` ("html"), `autoOpen` (true), `timeoutMs` (300000)
    - Apply the same change to all config copies: `RJ2XCL/Install/verify_payload/rj2xcl-config.json`, `RJ2XCL/Install/test_payload/rj2xcl-config.json`, `RJ2XCL/Install/_staging/rj2xcl-config.json`, `RJ2XCL/build_new/Dist/rj2xcl-config.json`
    - _Requirements: 8.1, 8.2_

  - [x] 1.2 Add Quarto getter methods to `ConfigService.h`
    - Add `GetQuartoConfig()`, `IsQuartoEnabled()`, `GetQuartoPath()`, `GetQuartoOutputDirectory()`, `GetQuartoDefaultFormat()`, `IsQuartoAutoOpen()`, `GetQuartoTimeoutMs()` inline methods to `RJ2XCL/Common/ConfigService.h`
    - `GetQuartoTimeoutMs()` must clamp to [5000, 1800000], defaulting to 300000 for non-positive values
    - `GetQuartoDefaultFormat()` must fall back to `"html"` for invalid values
    - Add Doxygen comments on each new method, consistent with existing getter style
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_

  - [x] 1.3 Extend `ConfigService::ValidateConfig()` for Quarto paths
    - In `RJ2XCL/Common/ConfigService.cc`, add validation of `Quarto.path` and `Quarto.outputDirectory` against path traversal (`..`) and command injection characters (`|`, `&`, `;`, `` ` ``, `<`, `>`), consistent with existing `ValidateConfig` patterns
    - _Requirements: 8.6_

  - [ ]* 1.4 Write unit tests for ConfigService Quarto getters
    - Create `RJ2XCL/Tests/quarto_config_tests.cc`
    - Test timeout clamping: 0 → 300000, 1000 → 5000, 999999 → 999999, 2000000 → 1800000
    - Test default format fallback: `"html"` → `"html"`, `"pdf"` → `"pdf"`, `"xlsx"` → `"html"`, `""` → `"html"`
    - Test missing Quarto section → all defaults
    - Test `IsQuartoEnabled()` with true, false, and missing values
    - Add `quarto_config_tests.cc` to `RJ2XCL/Tests/CMakeLists.txt`
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [x] 2. Checkpoint — Configuration compiles and existing tests pass
  - Ensure all existing tests pass, ask the user if questions arise.

- [x] 3. Create QuartoService core with input validation
  - [x] 3.1 Create `QuartoService.h` with class declaration
    - Create `RJ2XCL/Common/QuartoService.h` with the `rj2xcl::QuartoService` singleton class
    - Declare public methods: `Instance()`, `Initialize()`, `IsAvailable()`, `IsEnabled()`, `Render()`
    - Declare private methods: `DiscoverQuartoCLI()`, `ValidateExecutable()`, `ValidateInputSecurity()`, `ValidateFormat()`, `ResolveFilePath()`, `ValidateExtension()`, `SpawnRender()`, `SerializeToCSV()`, `EnsureOutputDirectory()`
    - Declare private state: `initialized_`, `enabled_`, `available_`, `quarto_path_`, `output_directory_`, `default_format_`, `auto_open_`, `timeout_ms_`
    - _Requirements: 1.1, 2.1, 2.2, 11.1, 11.2_

  - [x] 3.2 Implement input validation methods in `QuartoService.cc`
    - Create `RJ2XCL/Common/QuartoService.cc`
    - Implement `ValidateInputSecurity()`: block `..`, `|`, `&`, `;`, `` ` ``, `<`, `>` in input strings; return `BLOCKED:` error messages
    - Implement `ValidateExtension()`: accept only `.qmd` (case-insensitive)
    - Implement `ValidateFormat()`: accept `html`, `pdf`, `docx` (case-insensitive), normalize to lowercase
    - Implement `ResolveFilePath()`: absolute paths pass through unchanged, relative paths resolve against `output_directory_`
    - Implement output path construction: replace `.qmd` extension with the target format extension
    - Add `QuartoService.cc` to `RJ2XCL/Common/CMakeLists.txt` COMMON_SOURCES
    - _Requirements: 3.1, 3.2, 3.4, 3.5, 4.1, 4.2, 4.3, 5.5, 11.1, 11.2, 11.3, 11.4, 11.5_

  - [ ]* 3.3 Write property test: Path resolution preserves absolute, resolves relative
    - **Property 1: Path Resolution Preserves Absolute, Resolves Relative**
    - Create `RJ2XCL/Tests/quarto_service_pbt.cc`
    - Generate random absolute paths (drive letter prefix) and relative paths; verify absolute paths pass through unchanged and relative paths are joined with the output directory
    - Add `quarto_service_pbt.cc` to `RJ2XCL/Tests/CMakeLists.txt`
    - **Validates: Requirements 3.1, 3.2**

  - [ ]* 3.4 Write property test: Extension validation accepts only .qmd
    - **Property 2: Extension Validation Accepts Only .qmd**
    - Add to `RJ2XCL/Tests/quarto_service_pbt.cc`
    - Generate random file paths with various extensions; verify `.qmd` (any case) is accepted and all others are rejected
    - **Validates: Requirements 3.4, 3.5**

  - [ ]* 3.5 Write property test: Format validation and normalization
    - **Property 3: Format Validation and Normalization**
    - Add to `RJ2XCL/Tests/quarto_service_pbt.cc`
    - Generate random strings; verify only `html`/`pdf`/`docx` (case-insensitive) are accepted and normalized to lowercase
    - **Validates: Requirements 4.1, 4.2, 4.3**

  - [ ]* 3.6 Write property test: Input security validation blocks dangerous characters
    - **Property 6: Input Security Validation Blocks Dangerous Characters**
    - Add to `RJ2XCL/Tests/quarto_service_pbt.cc`
    - Generate strings with and without blocked characters; verify blocked strings return false with non-empty error, clean strings return true
    - **Validates: Requirements 8.6, 11.1, 11.2, 11.3, 11.4, 11.5**

  - [ ]* 3.7 Write property test: Output path construction
    - **Property 7: Output Path Construction**
    - Add to `RJ2XCL/Tests/quarto_service_pbt.cc`
    - Generate `.qmd` paths and valid formats; verify the `.qmd` extension is replaced with the correct output extension
    - **Validates: Requirements 5.5**

- [x] 4. Checkpoint — Validation logic compiles and tests pass
  - Ensure all tests pass (existing + new), ask the user if questions arise.

- [x] 5. Implement QuartoService initialization and CLI discovery
  - [x] 5.1 Implement `Initialize()` and `DiscoverQuartoCLI()`
    - Implement `QuartoService::Initialize()`: read config via `ConfigService`, expand environment variables in `output_directory_` and `quarto_path_` using `ExpandEnvironmentStringsA`, discover CLI, create output directory
    - Implement `DiscoverQuartoCLI()`: if `Quarto.path` is configured, use it; otherwise search PATH via `SearchPathA` for `quarto.exe`
    - Implement `ValidateExecutable()`: check file attributes via `GetFileAttributesA`
    - Implement `EnsureOutputDirectory()`: create output directory recursively via `CreateDirectoryA`
    - If Quarto is disabled or CLI not found, set `available_ = false` and return without error
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 9.1, 9.2_

  - [ ]* 5.2 Write property test: Timeout clamping
    - **Property 4: Timeout Clamping**
    - Add to `RJ2XCL/Tests/quarto_service_pbt.cc`
    - Generate random integers across full int range; verify `GetQuartoTimeoutMs()` returns values in [5000, 1800000] with correct clamping and default behavior
    - **Validates: Requirements 8.3**

  - [ ]* 5.3 Write property test: Config default format fallback
    - **Property 5: Config Default Format Fallback**
    - Add to `RJ2XCL/Tests/quarto_service_pbt.cc`
    - Generate random strings; verify `GetQuartoDefaultFormat()` returns one of `html`/`pdf`/`docx`, falling back to `html` for invalid values
    - **Validates: Requirements 8.4**

- [x] 6. Implement CSV data export and process spawning
  - [x] 6.1 Implement `SerializeToCSV()` for XLOPER12 data export
    - Implement CSV serialization of `XLOPER12` multi-arrays: handle `xltypeNum`, `xltypeStr` (with quote escaping), `xltypeBool`, `xltypeInt`, `xltypeNil`/`xltypeMissing`, `xltypeErr`
    - Write CSV with UTF-8 encoding, comma delimiter, CRLF line endings
    - Use deterministic filename: `<qmd_stem>_data.csv` in the output directory
    - _Requirements: 14.1, 14.2_

  - [x] 6.2 Implement `SpawnRender()` with process management
    - Implement `SpawnRender()`: build command line `quarto render <file> --to <format>`, create stderr capture pipe with `CreatePipe`, spawn via `CreateProcessA` with working directory set to the QMD file's parent directory
    - Set environment variables `RJ2XCL_DATA` (CSV path) and `RJ2XCL_EXCEL` ("true") in child process
    - Wait with `WaitForSingleObject` using configured timeout; on timeout, call `TerminateProcess`
    - Close write end of stderr pipe before reading; read last 500 chars of stderr on failure
    - Wrap all handles in `UniqueHandle` RAII wrappers
    - _Requirements: 5.1, 5.2, 5.3, 5.6, 6.1, 6.2, 6.3, 7.1, 7.5, 12.1, 12.2, 12.3, 12.4, 14.3, 14.4_

  - [x] 6.3 Implement `Render()` orchestration method
    - Implement the main `Render()` method: validate security → resolve path → check file exists → validate extension → validate format → serialize data (if provided) → ensure output directory → spawn render → check output file → auto-open (if enabled) → cleanup temp CSV → return result
    - Add logging: INFO on render start (file, format, timeout), INFO on success (output path, elapsed ms), ERROR on failure (exit code, stderr), WARN on timeout
    - _Requirements: 3.3, 5.4, 7.2, 7.3, 7.4, 10.1, 10.2, 10.3, 13.1, 13.2, 13.3, 13.4, 14.5_

  - [ ]* 6.4 Write property test: CSV serialization preserves cell data
    - **Property 8: CSV Serialization Preserves Cell Data**
    - Add to `RJ2XCL/Tests/quarto_service_pbt.cc`
    - Generate random cell data arrays with numeric, string, boolean, and empty values; verify CSV round-trip preserves dimensions, numeric precision, string content (including commas, quotes, newlines), and boolean values
    - **Validates: Requirements 14.2**

  - [ ]* 6.5 Write unit tests for QuartoService
    - Create `RJ2XCL/Tests/quarto_service_tests.cc`
    - Test path resolution: absolute passthrough, relative resolution, UNC path passthrough
    - Test extension validation: `.qmd` variants accepted, other extensions rejected
    - Test format validation: valid formats normalized, invalid formats rejected with correct error message
    - Test security validation: path traversal blocked, command injection chars blocked, clean paths accepted
    - Test output path construction: `.qmd` → `.html`/`.pdf`/`.docx`, multi-dot filenames
    - Test CSV serialization: numeric, string (with commas/quotes/newlines), boolean, empty cells, mixed types
    - Add `quarto_service_tests.cc` to `RJ2XCL/Tests/CMakeLists.txt`
    - _Requirements: 3.1, 3.2, 3.4, 3.5, 4.1, 4.2, 4.3, 5.5, 11.1, 11.2, 14.2_

- [x] 7. Checkpoint — QuartoService compiles and all tests pass
  - Ensure all tests pass (existing + new), ask the user if questions arise.

- [x] 8. Register RJ2XCL.Q function and wire into XLL
  - [x] 8.1 Add `RJ_Q` export declaration and `funcTemplates` entry
    - In `RJ2XCL/RJ2XCL/include/basic_functions.h`, add the export declaration: `extern "C" __declspec(dllexport) LPXLOPER12 WINAPI RJ_Q(LPXLOPER12 file_path, LPXLOPER12 format, LPXLOPER12 data_range);`
    - Add the `funcTemplates` entry before the `{ 0 }` sentinel: `{ L"RJ_Q", L"UQQQ", L"RJ2XCL.Q", L"FilePath, Format, DataRange", L"1", L"RJ2XCL", L"", L"", L"Render a Quarto document to HTML, PDF, or Word", L"Path to .qmd file", L"Output format: html, pdf, or docx (optional)", L"Excel range with data to pass to the document (optional)", L"", L"", L"", L"" }`
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 15.1_

  - [x] 8.2 Implement `RJ_Q` export function
    - In `RJ2XCL/RJ2XCL/src/basic_functions.cc`, implement the `RJ_Q` export function
    - Check `IsEnabled()` and `IsAvailable()` first, returning appropriate error strings
    - Extract string arguments from XLOPER12, pass `data_range` through as-is if not `xltypeMissing`
    - Call `QuartoService::Instance().Render()` and return the result string via `Convert::StringToXLOPER`
    - Use `thread_local XLOPER12` for the return value with `xlbitDLLFree` flag
    - _Requirements: 1.1, 1.4, 7.2, 7.3, 15.1_

  - [x] 8.3 Add QuartoService initialization to `rj2xcl.cc`
    - In `RJ2XCL/RJ2XCL/src/rj2xcl.cc`, add `#include "QuartoService.h"` and the initialization call `rj2xcl::QuartoService::Instance().Initialize();` after `ConfigService::Initialize()` and before `RegisterFunctions()`
    - _Requirements: 2.1, 15.2, 15.3_

- [x] 9. Final checkpoint — Full regression
  - Ensure all tests pass (existing 200+ tests plus all new Quarto tests) with zero failures and zero modifications to existing tests
  - Verify `QuartoService` does not modify any shared state used by existing language services (LanguageManager, callback_info, pipe handles)
  - Verify the `RJ_Q` export name does not conflict with existing exports (`RJ_FunctionCall`, `RJ_ExecLanguage_`, `RJ_CallLanguage_`)
  - _Requirements: 15.1, 15.2, 15.3, 15.4_

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation against the full test suite
- Property tests validate the 8 correctness properties defined in the design document
- The export name is `RJ_Q` and the Excel function name is `RJ2XCL.Q`
- QuartoService is fully isolated — no changes to LanguageManager, pipe system, or Protobuf infrastructure
- All Windows handles use `UniqueHandle` RAII wrappers consistent with project conventions
