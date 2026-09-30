# Design Document: Quarto Integration (RJ2XCL.Q)

## Overview

This design adds a `RJ2XCL.Q` worksheet function that renders Quarto `.qmd` documents directly from Excel cells. Unlike the existing R/Julia/Python language services — which embed interpreters in long-running child processes communicating via Named Pipes + Protobuf — the Quarto integration is a **stateless utility function**: each invocation spawns `quarto render` via `CreateProcessA`, waits for completion, and returns the output file path as a string.

This is a deliberately **low-risk** addition. It does not modify the LanguageManager, callback infrastructure, pipe system, or any shared state. The entire feature lives in two new files (`QuartoService.h` and `QuartoService.cc`) plus minor additions to existing registration and configuration code.

### Design Decisions

| Decision | Choice | Rationale |
|------------------------|------------------------|------------------------|
| Function name | `RJ2XCL.Q` | Follows the `R.`, `J.`, `P.`, `Q.` single-letter convention |
| Export name | `RJ_Quarto` | Dedicated export — avoids collision with `RJ_FunctionCall`, `RJ_ExecLanguage_`, `RJ_CallLanguage_` |
| Architecture | Stateless per-call `CreateProcessA` | No persistent child process needed — Quarto CLI is self-contained |
| New files | `QuartoService.h` + `QuartoService.cc` in `Common/` | Keeps all Quarto logic isolated; no changes to language service infrastructure |
| CLI discovery | `SearchPathA` + config override | Consistent with how users expect PATH-based tools to work; config override for locked-down environments |
| Config section | `Quarto` key in `rj2xcl-config.json` | Follows existing pattern (`RJ2XCL.Python`, etc.) |
| Security | Reuse `SandboxVerifier`-style character blocking on FilePath/Format args | Defense-in-depth against command injection via cell formulas |
| Handle management | `UniqueHandle` RAII wrappers | Consistent with project-wide pattern; prevents handle leaks |
| Data export | CSV via `XLOPER12` → text serialization | Simple, universal format readable by R/Python/Julia inside `.qmd` |
| Registration | Added to `funcTemplates` in `basic_functions.h` + dedicated `RJ_Quarto` export | Registered alongside other core functions in Phase 1 of `RegisterBasicFunctions` |

### Risk Assessment

| Area | Risk | Mitigation |
|------------------------|------------------------|------------------------|
| Existing tests | None — no shared state modified | `RJ_Quarto` is a new export; existing 200 tests untouched |
| LanguageManager | None — QuartoService is independent | No `LanguageService` subclass; no pipe/protobuf involvement |
| Excel stability | Low — synchronous `WaitForSingleObject` blocks the calling thread | Configurable timeout (default 5 min) with `TerminateProcess` fallback |
| Security | Low — file path and format validated before `CreateProcessA` | Character blocklist + `.qmd` extension check + path traversal check |

## Architecture

### System Context

``` mermaid
graph LR
    Excel["Excel (RJ2XCL64.xll)"] -->|Named Pipes + Protobuf| CR["ControlR.exe"]
    Excel -->|Named Pipes + Protobuf| CJ["ControlJulia.exe"]
    Excel -->|Named Pipes + Protobuf| CP["ControlPython.exe"]
    Excel -->|"CreateProcessA (per call)"| QC["quarto render (CLI)"]
    
    subgraph "XLL — Existing Components"
        LM["LanguageManager"]
        CS["ConfigService"]
        SV["SandboxVerifier"]
    end
    
    subgraph "XLL — New Component"
        QS["QuartoService"]
    end
    
    QS -->|reads config| CS
    QS -->|validates input| SV
    QS -->|spawns| QC
    QC -->|writes| Output["report.html / .pdf / .docx"]
```

### Call Flow

``` mermaid
sequenceDiagram
    participant User as Excel Cell
    participant XLL as RJ_Quarto (XLL export)
    participant QS as QuartoService
    participant CS as ConfigService
    participant FS as Filesystem
    participant CLI as quarto render

    User->>XLL: =RJ2XCL.Q("report.qmd", "html")
    XLL->>QS: Render(filePath, format, dataRange)
    
    QS->>QS: ValidateInputSecurity(filePath, format)
    alt Blocked characters detected
        QS-->>XLL: "BLOCKED: Path contains invalid characters"
    end
    
    QS->>CS: GetQuartoConfig()
    QS->>QS: ResolveFilePath(filePath, outputDir)
    QS->>FS: GetFileAttributesA(resolvedPath)
    alt File not found
        QS-->>XLL: "ERROR: File not found: <path>"
    end
    
    QS->>QS: ValidateExtension(resolvedPath)
    QS->>QS: ValidateFormat(format)
    
    opt DataRange provided
        QS->>QS: SerializeXLOPERToCSV(dataRange) → temp CSV
        QS->>QS: SetEnvironmentVariable("RJ2XCL_DATA", csvPath)
    end
    
    QS->>FS: CreateDirectoryA(outputDir) if needed
    QS->>CLI: CreateProcessA("quarto render <file> --to <fmt>")
    QS->>CLI: WaitForSingleObject(hProcess, timeoutMs)
    
    alt Timeout
        QS->>CLI: TerminateProcess(hProcess)
        QS-->>XLL: "ERROR: Quarto render timed out after N seconds"
    else Exit code ≠ 0
        QS->>QS: ReadStderr(pipe, 500 chars)
        QS-->>XLL: "ERROR: Quarto render failed (exit N): <stderr>"
    else Success
        QS->>FS: GetFileAttributesA(expectedOutputPath)
        opt autoOpen = true
            QS->>FS: ShellExecuteA("open", outputPath)
        end
        QS-->>XLL: outputPath
    end
    
    opt DataRange was provided
        QS->>FS: DeleteFileA(tempCSV)
    end
    
    XLL-->>User: result string in cell
```

## Components and Interfaces

### 1. QuartoService — `Common/QuartoService.h` + `Common/QuartoService.cc`

Singleton service managing Quarto CLI discovery, configuration, and render execution. Follows the `ConfigService` / `SecurityService` singleton pattern.

``` cpp
namespace rj2xcl {

class QuartoService {
public:
    static QuartoService& Instance();

    /// Called once during Init(). Reads config, discovers CLI, creates output dir.
    void Initialize();

    /// Returns true if Quarto CLI was found and integration is enabled.
    bool IsAvailable() const;

    /// Returns true if integration is enabled in config.
    bool IsEnabled() const;

    /// Main render entry point. Called from RJ_Quarto export.
    /// Returns output file path on success, or "ERROR: ..." / "BLOCKED: ..." string.
    std::string Render(const std::string& file_path,
                       const std::string& format,
                       LPXLOPER12 data_range);  // nullable

private:
    QuartoService();

    // --- Discovery ---
    std::string DiscoverQuartoCLI();
    bool ValidateExecutable(const std::string& path);

    // --- Input validation ---
    bool ValidateInputSecurity(const std::string& input, std::string& error_msg);
    bool ValidateFormat(const std::string& format, std::string& error_msg);
    std::string ResolveFilePath(const std::string& file_path);
    bool ValidateExtension(const std::string& resolved_path);

    // --- Process management ---
    std::string SpawnRender(const std::string& resolved_path,
                            const std::string& format,
                            const std::string& csv_path);

    // --- Data export ---
    std::string SerializeToCSV(LPXLOPER12 data_range,
                               const std::string& qmd_stem);

    // --- Output directory ---
    bool EnsureOutputDirectory(std::string& error_msg);

    // --- State ---
    bool initialized_ = false;
    bool enabled_ = true;
    bool available_ = false;
    std::string quarto_path_;          // Resolved path to quarto.exe
    std::string output_directory_;     // Expanded output directory
    std::string default_format_;       // "html", "pdf", or "docx"
    bool auto_open_ = true;
    DWORD timeout_ms_ = 300000;        // 5 minutes default
};

} // namespace rj2xcl
```

### 2. Excel Function Export — `basic_functions.h` + `basic_functions.cc`

A new `RJ_Quarto` export function is added, following the pattern of `RJ_Console`, `RJ_Version`, etc.

``` cpp
// basic_functions.h — new declaration
extern "C" __declspec(dllexport) LPXLOPER12 WINAPI RJ_Quarto(
    LPXLOPER12 file_path,
    LPXLOPER12 format,
    LPXLOPER12 data_range);
```

``` cpp
// basic_functions.cc — new implementation
extern "C" __declspec(dllexport) LPXLOPER12 WINAPI RJ_Quarto(
    LPXLOPER12 file_path, LPXLOPER12 format, LPXLOPER12 data_range) {

    thread_local XLOPER12 rslt;

    auto& qs = rj2xcl::QuartoService::Instance();

    if (!qs.IsEnabled()) {
        Convert::StringToXLOPER(&rslt,
            "ERROR: Quarto integration is disabled in configuration", false);
        rslt.xltype |= xlbitDLLFree;
        return &rslt;
    }
    if (!qs.IsAvailable()) {
        Convert::StringToXLOPER(&rslt,
            "ERROR: Quarto CLI not found. Install Quarto or configure "
            "Quarto.path in rj2xcl-config.json", false);
        rslt.xltype |= xlbitDLLFree;
        return &rslt;
    }

    // Extract string arguments
    std::string path_str = (file_path && file_path->xltype == xltypeStr)
        ? Convert::XLOPERToString(file_path) : "";
    std::string fmt_str = (format && format->xltype == xltypeStr)
        ? Convert::XLOPERToString(format) : "";

    // data_range passed through as-is (may be xltypeMulti, xltypeMissing, etc.)
    LPXLOPER12 data = (data_range && data_range->xltype != xltypeMissing)
        ? data_range : nullptr;

    std::string result = qs.Render(path_str, fmt_str, data);
    Convert::StringToXLOPER(&rslt, result.c_str(), false);
    rslt.xltype |= xlbitDLLFree;
    return &rslt;
}
```

### 3. Function Registration — `basic_functions.h` funcTemplates

A new entry is added to the `funcTemplates` array:

``` cpp
// In funcTemplates[] — before the { 0 } sentinel
{ L"RJ_Quarto", L"UQQQ", L"RJ2XCL.Q", L"FilePath, Format, DataRange",
  L"1", L"RJ2XCL", L"", L"",
  L"Render a Quarto document to HTML, PDF, or Word",
  L"Path to .qmd file",
  L"Output format: html, pdf, or docx (optional)",
  L"Excel range with data to pass to the document (optional)",
  L"", L"", L"", L"" },
```

The type signature `UQQQ` means: returns `XLOPER12` (U), takes three `XLOPER12` arguments (Q, Q, Q). The `Q` type auto-coerces Excel references to values, which is what we need.

### 4. ConfigService Extension — `Common/ConfigService.h`

New getter methods for Quarto configuration:

``` cpp
// ConfigService.h — new methods

/// Returns the full Quarto configuration section.
json11::Json GetQuartoConfig() const {
    return config_["Quarto"];
}

/// Returns true if Quarto integration is enabled (default: true).
bool IsQuartoEnabled() const {
    if (config_["Quarto"]["enabled"].is_bool())
        return config_["Quarto"]["enabled"].bool_value();
    return true;
}

/// Returns the configured Quarto CLI path (empty = auto-discover).
std::string GetQuartoPath() const {
    return config_["Quarto"]["path"].string_value();
}

/// Returns the Quarto output directory (with env vars unexpanded).
std::string GetQuartoOutputDirectory() const {
    std::string dir = config_["Quarto"]["outputDirectory"].string_value();
    return dir.empty() ? "%USERPROFILE%\\Documents\\RJ2XCL\\reports" : dir;
}

/// Returns the default output format (html, pdf, or docx).
std::string GetQuartoDefaultFormat() const {
    std::string fmt = config_["Quarto"]["defaultFormat"].string_value();
    if (fmt != "html" && fmt != "pdf" && fmt != "docx") return "html";
    return fmt;
}

/// Returns true if auto-open is enabled (default: true).
bool IsQuartoAutoOpen() const {
    if (config_["Quarto"]["autoOpen"].is_bool())
        return config_["Quarto"]["autoOpen"].bool_value();
    return true;
}

/// Returns the Quarto render timeout in milliseconds.
/// Default: 300000 (5 min). Clamped to [5000, 1800000].
DWORD GetQuartoTimeoutMs() const {
    int val = config_["Quarto"]["timeoutMs"].int_value();
    if (val < 5000) return (val > 0) ? 5000 : 300000;
    if (val > 1800000) return 1800000;
    return (DWORD)val;
}
```

The existing `ValidateConfig()` method is extended to validate `Quarto.path` and `Quarto.outputDirectory` against path traversal and command injection patterns, consistent with existing validation.

### 5. Initialization Hook — `rj2xcl.cc`

A single line is added to `RJ2XCL_Engine::Init()`, after `ConfigService::Initialize()` and before `RegisterFunctions()`:

``` cpp
// In RJ2XCL_Engine::Init(), after config_service.Initialize()
rj2xcl::QuartoService::Instance().Initialize();
```

This is the only change to `rj2xcl.cc`. The `QuartoService::Initialize()` call reads config, discovers the CLI, and creates the output directory. If Quarto is disabled or the CLI is not found, it simply sets `available_ = false` and returns — no error, no impact on startup.

## Data Models

### Configuration Schema (`rj2xcl-config.json`)

``` json
{
    "Quarto": {
        "enabled": true,
        "path": "",
        "outputDirectory": "%USERPROFILE%\\Documents\\RJ2XCL\\reports",
        "defaultFormat": "html",
        "autoOpen": true,
        "timeoutMs": 300000
    }
}
```

| Key | Type | Default | Validation |
|------------------|------------------|------------------|------------------|
| `enabled` | boolean | `true` | — |
| `path` | string | `""` (auto-discover) | No `..`, `|`, `&`, `;`, `` ` ``, `<`, `>` |
| `outputDirectory` | string | `%USERPROFILE%\Documents\RJ2XCL\reports` | Same as `path` |
| `defaultFormat` | string | `"html"` | Must be `html`, `pdf`, or `docx` |
| `autoOpen` | boolean | `true` | — |
| `timeoutMs` | integer | `300000` (5 min) | Clamped to \[5000, 1800000\] |

### CSV Serialization Format (DataRange → temp file)

When the optional `DataRange` argument is provided, the XLOPER12 multi-array is serialized to CSV:

| XLOPER12 Type | CSV Representation |
|------------------------------------|------------------------------------|
| `xltypeNum` | Decimal number (e.g., `3.14`) |
| `xltypeStr` | Double-quoted string with escaped quotes (e.g., `"hello ""world"""`) |
| `xltypeBool` | `TRUE` or `FALSE` |
| `xltypeInt` | Integer (e.g., `42`) |
| `xltypeNil` / `xltypeMissing` | Empty field |
| `xltypeErr` | `#ERROR` |

The CSV file is written with: - UTF-8 encoding (no BOM) - Comma delimiter - CRLF line endings (Windows convention) - Deterministic filename: `<qmd_stem>_data.csv` in the output directory

### Process Environment Variables

| Variable | Value | Purpose |
|------------------------|------------------------|------------------------|
| `RJ2XCL_DATA` | Absolute path to temp CSV | Allows `.qmd` code to read Excel data |
| `RJ2XCL_EXCEL` | `"true"` | Allows `.qmd` code to detect Excel context |

### Error String Format

All error strings follow a consistent prefix convention:

| Prefix     | Meaning                                                    |
|------------|------------------------------------------------------------|
| `ERROR:`   | Operational error (file not found, render failed, timeout) |
| `BLOCKED:` | Security validation rejected the input                     |

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Path Resolution Preserves Absolute, Resolves Relative

*For any* file path string, if the path is absolute (starts with a drive letter like `C:\` or `\\`), the resolved path SHALL equal the input unchanged. If the path is relative (no drive letter prefix), the resolved path SHALL equal the configured output directory joined with the relative path using a backslash separator.

**Validates: Requirements 3.1, 3.2**

### Property 2: Extension Validation Accepts Only .qmd

*For any* file path string, the extension validation SHALL return true if and only if the path ends with `.qmd` (case-insensitive). Paths ending with `.QMD`, `.Qmd`, or any other case variation SHALL be accepted. Paths with any other extension (`.html`, `.pdf`, `.txt`, `.qmd.bak`, etc.) or no extension SHALL be rejected.

**Validates: Requirements 3.4, 3.5**

### Property 3: Format Validation and Normalization

*For any* string, the format validation SHALL accept the string if and only if its lowercase form is one of `html`, `pdf`, or `docx`. When accepted, the normalized output SHALL be the lowercase form of the input. When rejected, the error message SHALL contain the original input value.

**Validates: Requirements 4.1, 4.2, 4.3**

### Property 4: Timeout Clamping

*For any* integer value provided as `Quarto.timeoutMs`, the `GetQuartoTimeoutMs()` getter SHALL return a value in the range \[5000, 1800000\]. Values below 5000 (but positive) SHALL be clamped to 5000. Values above 1800000 SHALL be clamped to 1800000. Non-positive values SHALL return the default of 300000.

**Validates: Requirements 8.3**

### Property 5: Config Default Format Fallback

*For any* string value provided as `Quarto.defaultFormat`, the `GetQuartoDefaultFormat()` getter SHALL return one of `html`, `pdf`, or `docx`. If the input is not one of these three values, the getter SHALL return `html`.

**Validates: Requirements 8.4**

### Property 6: Input Security Validation Blocks Dangerous Characters

*For any* string containing at least one character from the blocked set (`..`, `|`, `&`, `;`, `` ` ``, `<`, `>`), the `ValidateInputSecurity` function SHALL return false with a non-empty error message. *For any* string composed only of alphanumeric characters, backslashes, forward slashes, dots (not `..`), underscores, hyphens, spaces, and colons, the function SHALL return true.

**Validates: Requirements 8.6, 11.1, 11.2, 11.3, 11.4, 11.5**

### Property 7: Output Path Construction

*For any* file path ending in `.qmd` (case-insensitive) and *for any* valid format (`html`, `pdf`, `docx`), the constructed output path SHALL replace the `.qmd` extension with the corresponding output extension (`.html`, `.pdf`, `.docx`). The stem of the filename and all directory components SHALL remain unchanged.

**Validates: Requirements 5.5**

### Property 8: CSV Serialization Preserves Cell Data

*For any* XLOPER12 multi-array with dimensions (rows \> 0, cols \> 0) containing numeric, string, boolean, or empty values, serializing to CSV and parsing back SHALL preserve: (a) the number of rows and columns, (b) numeric values within floating-point precision, (c) string values exactly (including those containing commas, quotes, and newlines), and (d) boolean values as `TRUE`/`FALSE`.

**Validates: Requirements 14.2**

## Error Handling

### Error Categories and Messages

| Condition | Error String | Severity |
|------------------------|------------------------|------------------------|
| Integration disabled | `ERROR: Quarto integration is disabled in configuration` | INFO |
| CLI not found | `ERROR: Quarto CLI not found. Install Quarto or configure Quarto.path in rj2xcl-config.json` | WARN |
| File not found | `ERROR: File not found: <resolved_path>` | ERROR |
| Wrong extension | `ERROR: File must have .qmd extension` | ERROR |
| Invalid format | `ERROR: Unsupported format '<value>'. Use html, pdf, or docx` | ERROR |
| Path injection | `BLOCKED: Path contains invalid characters` | WARN |
| Format injection | `BLOCKED: Format contains invalid characters` | WARN |
| CreateProcess failed | `ERROR: Failed to start Quarto process (Windows error <code>)` | ERROR |
| Render failed (exit ≠ 0) | `ERROR: Quarto render failed (exit <code>): <stderr_last_500_chars>` | ERROR |
| Render timeout | `ERROR: Quarto render timed out after <seconds> seconds` | WARN |
| Output file missing | `ERROR: Render completed but output file not found at <expected_path>` | ERROR |
| Output dir creation failed | `ERROR: Cannot create output directory: <path>` | ERROR |
| ShellExecuteA failed | *(non-fatal — output path still returned, warning logged)* | WARN |

### Error Handling Strategy

1.  **Fail-fast validation**: All input validation (security, extension, format) happens before any process spawning or filesystem operations. This minimizes resource usage on invalid inputs.

2.  **RAII for all handles**: Every `HANDLE` from `CreateProcessA` and `CreatePipe` is wrapped in `UniqueHandle`. This guarantees cleanup even if an exception or early return occurs mid-function.

3.  **Stderr capture with truncation**: The child process stderr is captured via a pipe. Only the last 500 characters are included in error messages to prevent excessively long cell values.

4.  **Timeout with forced termination**: If `WaitForSingleObject` returns `WAIT_TIMEOUT`, the child process is terminated via `TerminateProcess`. The process and thread handles are then closed via RAII.

5.  **Non-fatal auto-open**: `ShellExecuteA` failure is logged but does not change the return value. The user still gets the output file path.

6.  **Temp CSV cleanup**: The temporary CSV file is deleted in a `finally`-style cleanup block (using RAII or explicit cleanup before return), regardless of whether the render succeeded or failed.

### Pipe Deadlock Prevention

The stderr capture pipe follows the standard Windows pattern to avoid deadlocks:

1.  Create pipe with `CreatePipe(&hReadPipe, &hWritePipe, ...)`
2.  Pass `hWritePipe` to `STARTUPINFOA.hStdError`
3.  **Close `hWritePipe` in the parent process** immediately after `CreateProcessA` succeeds
4.  Read from `hReadPipe` after `WaitForSingleObject` completes
5.  Close `hReadPipe` via RAII

Closing the write end before reading ensures that `ReadFile` on the read end will return when the child process exits, rather than blocking indefinitely.

## Testing Strategy

### Unit Tests (GTest)

The primary unit-testable components are the pure functions in `QuartoService`:

**Path resolution tests:** - Absolute path passthrough (`C:\reports\test.qmd` → unchanged) - Relative path resolution (`test.qmd` → `outputDir\test.qmd`) - UNC path passthrough (`\\server\share\test.qmd` → unchanged)

**Extension validation tests:** - `.qmd` accepted (various cases: `.QMD`, `.Qmd`, `.qMd`) - `.html`, `.pdf`, `.txt`, `.qmd.bak`, no extension → rejected - Edge case: filename is exactly `.qmd`

**Format validation tests:** - `html`, `pdf`, `docx` accepted (various cases) - `pptx`, `latex`, `epub`, empty string → rejected with correct error message - Normalization: `HTML` → `html`, `PDF` → `pdf`, `DOCX` → `docx`

**Security validation tests:** - Path traversal: `..`, `..\`, `/../` → blocked - Command injection: `|`, `&`, `;`, `` ` ``, `<`, `>` → blocked - Clean paths: `C:\Users\test\report.qmd` → accepted - Edge cases: path with spaces, Unicode characters

**Config getter tests:** - Timeout clamping: 0 → 300000, 1000 → 5000, 999999 → 999999, 2000000 → 1800000 - Default format: `html` → `html`, `pdf` → `pdf`, `xlsx` → `html`, `""` → `html` - Missing Quarto section → all defaults

**CSV serialization tests:** - Numeric values: integers, floats, negative numbers - String values: plain, with commas, with quotes, with newlines - Boolean values: TRUE/FALSE - Empty cells: nil/missing → empty field - Mixed types in a single row

**Output path construction tests:** - `report.qmd` + `html` → `report.html` - `report.qmd` + `pdf` → `report.pdf` - `report.QMD` + `docx` → `report.docx` (case-insensitive replacement) - Path with multiple dots: `my.report.v2.qmd` + `html` → `my.report.v2.html`

### Property-Based Tests (GTest + custom generators)

Property-based tests validate the correctness properties defined above. Each test runs a minimum of **100 iterations** with randomly generated inputs.

**Library:** Custom generators within GTest (consistent with existing project pattern).

| Property | Test Description | Tag |
|------------------------|------------------------|------------------------|
| P1 | Generate random absolute and relative paths, verify resolution logic | `Feature: quarto-integration, Property 1: Path resolution preserves absolute, resolves relative` |
| P2 | Generate random file paths with various extensions, verify .qmd-only acceptance | `Feature: quarto-integration, Property 2: Extension validation accepts only .qmd` |
| P3 | Generate random strings, verify format validation and normalization | `Feature: quarto-integration, Property 3: Format validation and normalization` |
| P4 | Generate random integers across full int range, verify timeout clamping | `Feature: quarto-integration, Property 4: Timeout clamping` |
| P5 | Generate random strings, verify default format fallback | `Feature: quarto-integration, Property 5: Config default format fallback` |
| P6 | Generate random strings with/without blocked characters, verify security validation | `Feature: quarto-integration, Property 6: Input security validation blocks dangerous characters` |
| P7 | Generate random .qmd paths and valid formats, verify output path construction | `Feature: quarto-integration, Property 7: Output path construction` |
| P8 | Generate random cell data arrays, verify CSV round-trip | `Feature: quarto-integration, Property 8: CSV serialization preserves cell data` |

### Integration Tests

Integration tests require a Quarto CLI installation on the test machine:

- **CLI discovery**: Verify `DiscoverQuartoCLI()` finds Quarto when installed, returns empty when not.
- **End-to-end render**: Create a minimal `.qmd` file, call `Render()`, verify output file exists.
- **Timeout behavior**: Create a `.qmd` with a long-running code chunk, set short timeout, verify termination and error message.
- **Data export**: Pass a cell range, verify the temp CSV is created with correct content, and `RJ2XCL_DATA` env var is set in the child process.
- **Auto-open**: Verify `ShellExecuteA` is called when `autoOpen=true` and not called when `false`.
- **Non-regression**: Run the full existing test suite (200 tests across 16+ suites) and verify all pass.

### Test File Organization

```         
tests/
├── quarto_service_tests.cc       # NEW — Unit tests for QuartoService pure functions
├── quarto_service_pbt.cc         # NEW — Property-based tests for QuartoService
├── quarto_config_tests.cc        # NEW — Unit tests for ConfigService Quarto getters
├── sandbox_tests.cc              # EXISTING — no changes needed
└── ...
```