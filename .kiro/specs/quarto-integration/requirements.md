# Requirements Document: Quarto Integration

## Introduction

This feature adds reproducible report generation to RJ2XCL by integrating Quarto CLI as a utility function callable directly from Excel cells. Unlike the existing R/Julia/Python language services (which use Named Pipes + Protobuf for IPC), the Quarto integration is a lightweight child process invocation — `quarto render` is spawned via `CreateProcessA`, waited on with a configurable timeout, and the output file path is returned to the Excel cell. This enables "Citizen Data Scientists" to generate HTML, PDF, and Word reports from `.qmd` files without leaving Excel.

## Glossary

- **XLL**: An Excel add-in DLL that registers custom worksheet functions via the `xlfRegister` API.
- **Quarto_CLI**: The `quarto` command-line executable (v1.9.18+) that renders `.qmd` files into output formats (HTML, PDF, Word).
- **QMD_File**: A Quarto Markdown file (`.qmd` extension) containing narrative text and code chunks in R, Python, or Julia.
- **Quarto_Function**: The new Excel worksheet function `RJ2XCL.Quarto` registered by the XLL via `xlfRegister`.
- **Quarto_Service**: The C++ module within the XLL that manages Quarto CLI discovery, configuration reading, process spawning, and result handling.
- **Output_Format**: One of the supported Quarto render targets: `html`, `pdf`, or `docx`.
- **Config_Service**: The existing `ConfigService` singleton that reads and validates `rj2xcl-config.json`.
- **Sandbox_Verifier**: The existing `SandboxVerifier` that validates user input against blocked patterns.
- **Output_Directory**: The configured directory where rendered report files are stored.
- **Auto_Open**: The optional behavior of opening the rendered output file automatically using `ShellExecuteA`.

## Requirements

### Requirement 1: Excel Function Registration

**User Story:** As an Excel user, I want a worksheet function `RJ2XCL.Quarto` available in the function wizard, so that I can render Quarto reports directly from a cell formula.

#### Acceptance Criteria

1.  WHEN the XLL is loaded by Excel, THE Quarto_Function SHALL be registered via `xlfRegister` with the signature `RJ2XCL.Quarto(FilePath, [Format])` under the "RJ2XCL" function category.
2.  THE Quarto_Function SHALL accept a first argument `FilePath` of type string specifying the path to a QMD_File.
3.  THE Quarto_Function SHALL accept an optional second argument `Format` of type string specifying the Output_Format.
4.  WHEN the `Format` argument is omitted, THE Quarto_Function SHALL use the default format configured in `rj2xcl-config.json` under `Quarto.defaultFormat`.
5.  THE Quarto_Function SHALL appear in the Excel Function Wizard with the description "Render a Quarto document to HTML, PDF, or Word" and argument help text for `FilePath` and `Format`.

### Requirement 2: Quarto CLI Discovery and Validation

**User Story:** As an Excel user, I want RJ2XCL to find the Quarto CLI automatically or use a configured path, so that I do not need to configure anything if Quarto is already in my PATH.

#### Acceptance Criteria

1.  WHEN the Quarto integration is enabled and no custom path is configured, THE Quarto_Service SHALL search for the `quarto` executable in the system PATH using `SearchPathA`.
2.  WHEN a custom path is configured in `Quarto.path`, THE Quarto_Service SHALL use that path instead of searching the system PATH.
3.  WHEN the Quarto_Service locates the executable, THE Quarto_Service SHALL verify it is executable by checking the file attributes via `GetFileAttributesA`.
4.  IF the Quarto CLI executable is not found in the system PATH and no custom path is configured, THEN THE Quarto_Service SHALL log a warning and set its status to unavailable.
5.  IF the configured custom path does not point to a valid executable, THEN THE Quarto_Service SHALL log an error with the invalid path and set its status to unavailable.

### Requirement 3: QMD File Path Resolution

**User Story:** As an Excel user, I want to specify QMD file paths as absolute or relative, so that I can organize my report files flexibly.

#### Acceptance Criteria

1.  WHEN the `FilePath` argument is an absolute path, THE Quarto_Service SHALL use it directly without modification.
2.  WHEN the `FilePath` argument is a relative path, THE Quarto_Service SHALL resolve it relative to the configured `Quarto.outputDirectory`.
3.  IF the resolved QMD_File does not exist, THEN THE Quarto_Function SHALL return the error string "ERROR: File not found: <resolved_path>".
4.  THE Quarto_Service SHALL validate that the resolved file path has a `.qmd` extension (case-insensitive).
5.  IF the file path does not have a `.qmd` extension, THEN THE Quarto_Function SHALL return the error string "ERROR: File must have .qmd extension".

### Requirement 4: Output Format Validation

**User Story:** As an Excel user, I want clear feedback when I specify an invalid output format, so that I can correct my formula quickly.

#### Acceptance Criteria

1.  THE Quarto_Function SHALL accept the following Output_Format values (case-insensitive): `html`, `pdf`, `docx`.
2.  IF the `Format` argument contains a value not in the supported set, THEN THE Quarto_Function SHALL return the error string "ERROR: Unsupported format '<value>'. Use html, pdf, or docx".
3.  THE Quarto_Service SHALL normalize the format value to lowercase before passing it to the Quarto CLI.

### Requirement 5: Quarto Render Execution

**User Story:** As an Excel user, I want the Quarto render process to execute reliably and return the output file path, so that I can locate and use the generated report.

#### Acceptance Criteria

1.  WHEN the Quarto_Function is called with valid arguments, THE Quarto_Service SHALL spawn a child process using `CreateProcessA` with the command `quarto render <file_path> --to <format>`.
2.  THE Quarto_Service SHALL set the child process working directory to the directory containing the QMD_File.
3.  THE Quarto_Service SHALL wait for the child process to complete using `WaitForSingleObject` with the configured `Quarto.timeoutMs` timeout.
4.  WHEN the child process completes with exit code 0, THE Quarto_Function SHALL return the absolute path to the generated output file as a string.
5.  THE Quarto_Service SHALL construct the expected output file path by replacing the `.qmd` extension with the appropriate output extension (`.html`, `.pdf`, or `.docx`).
6.  THE Quarto_Service SHALL redirect the child process `stdout` and `stderr` to pipes for capture using `CreatePipe` and `STARTUPINFOA` redirection.

### Requirement 6: Render Timeout Handling

**User Story:** As an Excel user, I want long-running renders to be terminated gracefully after a configurable timeout, so that Excel does not freeze indefinitely.

#### Acceptance Criteria

1.  WHEN the child process does not complete within `Quarto.timeoutMs` milliseconds, THE Quarto_Service SHALL terminate the child process using `TerminateProcess`.
2.  WHEN a timeout occurs, THE Quarto_Function SHALL return the error string "ERROR: Quarto render timed out after <seconds> seconds".
3.  THE Quarto_Service SHALL close all process and pipe handles after termination using RAII wrappers (`UniqueHandle`).

### Requirement 7: Render Error Handling

**User Story:** As an Excel user, I want descriptive error messages when a render fails, so that I can diagnose and fix problems in my QMD file.

#### Acceptance Criteria

1.  IF the child process exits with a non-zero exit code, THEN THE Quarto_Function SHALL return an error string containing the exit code and the last 500 characters of captured `stderr` output.
2.  IF the Quarto_Service is unavailable (CLI not found), THEN THE Quarto_Function SHALL return the error string "ERROR: Quarto CLI not found. Install Quarto or configure Quarto.path in rj2xcl-config.json".
3.  IF the Quarto integration is disabled in configuration, THEN THE Quarto_Function SHALL return the error string "ERROR: Quarto integration is disabled in configuration".
4.  IF the expected output file does not exist after a successful process exit, THEN THE Quarto_Function SHALL return the error string "ERROR: Render completed but output file not found at <expected_path>".
5.  IF `CreateProcessA` fails to spawn the child process, THEN THE Quarto_Function SHALL return an error string containing the Windows error code from `GetLastError`.

### Requirement 8: Configuration Extension

**User Story:** As an administrator, I want to configure Quarto integration settings in `rj2xcl-config.json`, so that I can control behavior without modifying code.

#### Acceptance Criteria

1.  THE Config_Service SHALL read a `Quarto` section from `rj2xcl-config.json` with the following keys: `enabled` (boolean), `path` (string), `outputDirectory` (string), `defaultFormat` (string), `autoOpen` (boolean), `timeoutMs` (integer).
2.  WHEN the `Quarto` section is absent from the configuration file, THE Config_Service SHALL use these defaults: `enabled=true`, `path=""`, `outputDirectory="%USERPROFILE%\\Documents\\RJ2XCL\\reports"`, `defaultFormat="html"`, `autoOpen=true`, `timeoutMs=300000`.
3.  THE Config_Service SHALL validate that `Quarto.timeoutMs` is within the range \[5000, 1800000\] milliseconds and clamp out-of-range values to the nearest bound.
4.  THE Config_Service SHALL validate that `Quarto.defaultFormat` is one of `html`, `pdf`, or `docx`, and fall back to `html` if the value is invalid.
5.  THE Config_Service SHALL expand environment variables in `Quarto.path` and `Quarto.outputDirectory` using `ExpandEnvironmentStringsA`.
6.  THE Config_Service SHALL validate `Quarto.path` and `Quarto.outputDirectory` against path traversal patterns (`..`) and command injection characters (`|`, `&`, `;`, `` ` ``), consistent with existing `ValidateConfig` behavior.

### Requirement 9: Output Directory Management

**User Story:** As an Excel user, I want the output directory to be created automatically if it does not exist, so that I do not need to create folders manually before rendering.

#### Acceptance Criteria

1.  WHEN the configured Output_Directory does not exist, THE Quarto_Service SHALL create it recursively using `CreateDirectoryA` (consistent with the existing functions directory creation pattern).
2.  IF the Output_Directory cannot be created due to permissions, THEN THE Quarto_Function SHALL return the error string "ERROR: Cannot create output directory: <path>".

### Requirement 10: Auto-Open Rendered Output

**User Story:** As an Excel user, I want the rendered report to open automatically in my default application, so that I can view results immediately.

#### Acceptance Criteria

1.  WHEN `Quarto.autoOpen` is true and the render completes successfully, THE Quarto_Service SHALL open the output file using `ShellExecuteA` with the "open" verb.
2.  WHEN `Quarto.autoOpen` is false, THE Quarto_Service SHALL return the output path without opening the file.
3.  IF `ShellExecuteA` fails, THEN THE Quarto_Service SHALL log a warning but still return the output file path to the cell (the open failure is non-fatal).

### Requirement 11: Input Security Validation

**User Story:** As a security-conscious user, I want the file path argument to be validated against injection attacks, so that malicious formulas cannot execute arbitrary commands.

#### Acceptance Criteria

1.  THE Quarto_Service SHALL validate the `FilePath` argument against path traversal sequences (`..`).
2.  THE Quarto_Service SHALL validate the `FilePath` argument against command injection characters (`|`, `&`, `;`, `` ` ``, `$`, `>`, `<`).
3.  IF the `FilePath` argument contains blocked characters, THEN THE Quarto_Function SHALL return the error string "BLOCKED: Path contains invalid characters".
4.  THE Quarto_Service SHALL validate the `Format` argument against command injection characters using the same pattern set.
5.  IF the `Format` argument contains blocked characters, THEN THE Quarto_Function SHALL return the error string "BLOCKED: Format contains invalid characters".

### Requirement 12: Process Resource Cleanup

**User Story:** As a developer, I want all Windows handles and resources to be cleaned up deterministically, so that the XLL does not leak handles during long Excel sessions.

#### Acceptance Criteria

1.  THE Quarto_Service SHALL manage all process handles (`HANDLE` from `CreateProcessA`) using `UniqueHandle` RAII wrappers.
2.  THE Quarto_Service SHALL manage all pipe handles (`HANDLE` from `CreatePipe`) using `UniqueHandle` RAII wrappers.
3.  THE Quarto_Service SHALL close the write end of the `stderr` capture pipe before reading from the read end, to prevent deadlocks.
4.  WHEN the Quarto_Function returns (success or error), all handles created during that invocation SHALL be closed.

### Requirement 13: Logging and Diagnostics

**User Story:** As a developer, I want Quarto render operations to be logged, so that I can diagnose issues from the log file.

#### Acceptance Criteria

1.  WHEN a render is initiated, THE Quarto_Service SHALL log an INFO message containing the QMD file path, output format, and timeout value.
2.  WHEN a render completes successfully, THE Quarto_Service SHALL log an INFO message containing the output file path and elapsed time in milliseconds.
3.  WHEN a render fails, THE Quarto_Service SHALL log an ERROR message containing the exit code, elapsed time, and captured stderr (truncated to 500 characters).
4.  WHEN a timeout occurs, THE Quarto_Service SHALL log a WARN message containing the file path and configured timeout value.

### Requirement 14: Excel Data Export to Quarto

**User Story:** As an Excel user, I want to pass cell data to my Quarto document, so that my reports can include live data from the spreadsheet.

#### Acceptance Criteria

1.  THE Quarto_Function SHALL accept an optional third argument `DataRange` of type XLOPER12 (range reference or value).
2.  WHEN a `DataRange` argument is provided, THE Quarto_Service SHALL serialize the cell data to a temporary CSV file in the Output_Directory with a deterministic name derived from the QMD file name (e.g., `reporte_data.csv`).
3.  THE Quarto_Service SHALL set the environment variable `RJ2XCL_DATA` to the absolute path of the temporary CSV file before spawning the child process.
4.  THE Quarto_Service SHALL set the environment variable `RJ2XCL_EXCEL` to `true` in the child process environment, so that QMD files can detect they are being rendered from Excel.
5.  WHEN the render completes (success or failure), THE Quarto_Service SHALL delete the temporary CSV file.

### Requirement 15: Non-Regression

**User Story:** As a developer, I want the Quarto integration to not break any existing functionality, so that the 200 existing tests continue to pass.

#### Acceptance Criteria

1.  THE Quarto_Function registration SHALL use a dedicated export function name (`RJ_Quarto`) that does not conflict with existing `RJ_FunctionCall`, `RJ_ExecLanguage_`, or `RJ_CallLanguage_` exports.
2.  WHEN the Quarto integration is disabled (`Quarto.enabled=false`), THE XLL SHALL skip Quarto function registration and Quarto CLI discovery entirely.
3.  THE Quarto_Service SHALL not modify any shared state used by the existing language services (LanguageManager, callback_info, pipe handles).
4.  ALL existing unit tests (200 tests across 16+ suites) SHALL continue to pass without modification after the Quarto integration is added.