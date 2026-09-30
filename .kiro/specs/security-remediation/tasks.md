# Implementation Plan: Security Remediation

## Overview

This plan implements the comprehensive security remediation for the NEVEN project, addressing 36 audit findings (8 critical, 7 high, 5 medium, 14 low) across input sanitization, sandbox hardening, build security, IPC validation, code cleanup, and documentation. Tasks are ordered by severity priority: critical/high first, then medium/low.

## Tasks

- [x] 1. Create Security module directory structure and core interfaces
  - [x] 1.1 Create Common/Security/ directory with InputSanitizer header and implementation stubs
    - Create `Common/Security/InputSanitizer.h` with the full interface (ValidatePath, ValidateArgument, SanitizePath, BuildSafeCommandLine)
    - Create `Common/Security/InputSanitizer.cc` with stub implementations
    - Define ValidationResult struct, error codes (NEVEN_ERR_INVALID_PATH_CHAR, NEVEN_ERR_EMPTY_PATH, NEVEN_ERR_PATH_TOO_LONG, NEVEN_ERR_NULL_INPUT)
    - Define character allowlists as private static methods (IsAllowedPathChar, IsAllowedArgumentChar)
    - _Requirements: 1.1, 1.2, 1.3, 1.5, 1.6_

  - [x] 1.2 Create Common/IPC/MessageValidator header and implementation stubs
    - Create `Common/IPC/MessageValidator.h` with ValidateFrame and SafeUnframe interfaces
    - Create `Common/IPC/MessageValidator.cc` with stub implementations
    - Define constants: kDefaultMaxMessageSize (64 MB), kMinFrameSize (4 bytes)
    - _Requirements: 7.1, 7.2, 7.3, 7.4_

  - [x] 1.3 Create Common/IPC/SafePipeHandle header and implementation stubs
    - Create `Common/IPC/SafePipeHandle.h` with RAII wrapper interface (AtomicRead, AtomicWrite, IsValid, Close)
    - Create `Common/IPC/SafePipeHandle.cc` with stub implementations
    - Implement move semantics, delete copy constructor/assignment
    - Include CRITICAL_SECTION member for atomic operations
    - _Requirements: 8.1, 8.2, 8.3_

  - [x] 1.4 Update Common/CMakeLists.txt to include new Security/ and IPC/ subdirectory sources
    - Add Security/InputSanitizer.cc to Common library sources
    - Add IPC/MessageValidator.cc and IPC/SafePipeHandle.cc to Common library sources
    - Ensure include paths are set correctly for the new subdirectories
    - _Requirements: 12.1, 12.2, 12.3, 12.4_

- [x] 2. Implement InputSanitizer (Critical — OS Command Injection)
  - [x] 2.1 Implement ValidatePath and ValidateArgument with character allowlist logic
    - Implement IsAllowedPathChar: [A-Za-z0-9], \, /, ., -, _, space, : (drive letter)
    - Implement IsAllowedArgumentChar: [A-Za-z0-9], ., -, _, space
    - ValidatePath returns ValidationResult with first_invalid_char and position
    - ValidateArgument rejects &, |, ;, `, <, >, ", \n, \r, %, $, !
    - Handle edge cases: empty path, path exceeding MAX_PATH (260), null-equivalent
    - _Requirements: 1.1, 1.2, 1.3, 1.5_

  - [x] 2.2 Write property test for InputSanitizer allowlist correctness
    - **Property 1: InputSanitizer allowlist correctness**
    - **Validates: Requirements 1.1, 1.2, 1.3, 1.5**
    - Test file: `tests/input_sanitizer_pbt.cc`
    - Generator: random strings with mixed allowed/disallowed characters
    - Assert: ValidatePath accepts iff all chars in allowlist; rejects iff any char outside

  - [x] 2.3 Implement SanitizePath with idempotence guarantee
    - Remove all characters not in the path allowlist
    - Ensure SanitizePath(SanitizePath(x)) == SanitizePath(x) for all inputs
    - Return sanitized string (may be empty if all chars removed)
    - _Requirements: 1.6_

  - [x] 2.4 Write property test for InputSanitizer idempotence
    - **Property 2: InputSanitizer idempotence**
    - **Validates: Requirements 1.6**
    - Test file: `tests/input_sanitizer_pbt.cc`
    - Generator: arbitrary strings (Unicode, control chars, metacharacters)
    - Assert: SanitizePath(SanitizePath(x)) == SanitizePath(x)

  - [x] 2.5 Implement BuildSafeCommandLine with lpApplicationName/lpCommandLine separation
    - Separate executable path into lpApplicationName parameter
    - Construct lpCommandLine with properly quoted arguments
    - Validate all inputs through ValidatePath/ValidateArgument before construction
    - _Requirements: 1.4_

  - [x] 2.6 Write unit tests for InputSanitizer
    - Test file: `tests/input_sanitizer_tests.cc`
    - Test CreateProcess separation (lpApplicationName vs lpCommandLine)
    - Test rejection of known metacharacters: &, |, ;, `, <, >, ", \n, \r, %
    - Test empty path, MAX_PATH exceeded, valid paths with drive letters
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6_

- [x] 3. Integrate InputSanitizer into existing CreateProcess call sites
  - [x] 3.1 Integrate InputSanitizer into RJ_Q function and ContentPipeline::ConvertWithPandoc
    - Add InputSanitizer::ValidatePath call before CreateProcessA in RJ_Q
    - Add InputSanitizer::ValidatePath call in ContentPipeline::ConvertWithPandoc
    - Use BuildSafeCommandLine for all CreateProcess calls
    - Return error codes to Excel on validation failure
    - _Requirements: 1.1, 1.2, 1.4_

  - [x] 3.2 Integrate InputSanitizer into QuartoService::ValidateInputSecurity
    - Add blocking of ", \n, \r, % in addition to existing &, |, ;, `, <, >
    - Use InputSanitizer::ValidateArgument for Quarto CLI arguments
    - _Requirements: 1.5_

- [x] 4. Checkpoint — Verify input sanitization
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Enhance SandboxVerifier (Critical — Sandbox Bypass)
  - [x] 5.1 Add ValidateFromAnySource unified entry point and ExecutionSource enum
    - Add ExecutionSource enum: ExcelCell, REPL, AutoLoader, RegisteredFunc
    - Implement ValidateFromAnySource that delegates to existing validation with source tracking
    - Ensure all execution paths produce identical verdicts for the same code
    - _Requirements: 3.1, 3.2_

  - [x] 5.2 Write property test for sandbox execution path equivalence
    - **Property 3: Sandbox execution path equivalence**
    - **Validates: Requirements 3.1, 3.2**
    - Test file: `tests/sandbox_path_pbt.cc`
    - Generator: random code strings
    - Assert: same verdict regardless of ExecutionSource (ExcelCell, REPL, AutoLoader)

  - [x] 5.3 Extend R blocklist with additional dangerous functions
    - Add: readLines (pipe arg), get, source, library, open, Sys.getenv, Sys.setenv, .Internal, .Call, .External, .C, .Fortran
    - Implement context-aware detection for readLines (pipe argument pattern)
    - _Requirements: 3.3, 10.1_

  - [x] 5.4 Extend Julia blocklist with additional dangerous functions
    - Add: unsafe_pointer_to_objref, unsafe_wrap, ENV[, ENV, open (process/Cmd detection), Sockets.connect
    - Implement context-aware detection for open with backtick/Cmd patterns
    - _Requirements: 3.4, 10.2_

  - [x] 5.5 Write property test for sandbox blocklist enforcement
    - **Property 4: Sandbox blocklist enforcement**
    - **Validates: Requirements 3.3, 3.4, 10.1, 10.2**
    - Test file: `tests/sandbox_blocklist_pbt.cc`
    - Generator: code strings with embedded blocked patterns (whitespace-stripped, case-normalized)
    - Assert: SandboxVerifier returns Blocked for any code containing a blocklisted pattern

  - [x] 5.6 Implement specific rejection messages identifying blocked function
    - Ensure rejection_reason contains the name of the blocked function/pattern
    - Include reason category (e.g., "file system access", "environment variable access", "network access")
    - _Requirements: 3.7, 10.3_

  - [x] 5.7 Write property test for sandbox error message specificity
    - **Property 5: Sandbox error message specificity**
    - **Validates: Requirements 3.7, 10.3**
    - Test file: `tests/sandbox_blocklist_pbt.cc`
    - Generator: code strings with a single known blocked pattern
    - Assert: rejection_reason contains the name of the blocked function

  - [x] 5.8 Ensure SandboxVerifier idempotence
    - Verify ValidateCodeForExecution produces same result on repeated calls with same input
    - No internal state mutation between calls
    - _Requirements: 3.8_

  - [x] 5.9 Write property test for sandbox verification idempotence
    - **Property 6: Sandbox verification idempotence**
    - **Validates: Requirements 3.8**
    - Test file: `tests/sandbox_path_pbt.cc`
    - Generator: arbitrary strings
    - Assert: ValidateFromAnySource(x) called twice produces identical boolean and rejection_reason

- [x] 6. Integrate SandboxVerifier into REPL and AutoLoader paths
  - [x] 6.1 Integrate SandboxVerifier::ValidateFromAnySource into REPL execution path
    - Modify REPLManager/REPLBridge to call ValidateFromAnySource with ExecutionSource::REPL
    - Ensure blocked code returns error message to REPL console
    - _Requirements: 3.1_

  - [x] 6.2 Integrate SandboxVerifier::ValidateFromAnySource into AutoLoader
    - Modify AutoLoader::SourcingRFiles and SourcingJuliaFiles to call ValidateFromAnySource
    - Use ExecutionSource::AutoLoader for audit trail
    - Log blocked scripts via LogService::Warning with filename and rejection reason
    - _Requirements: 3.2_

  - [x] 6.3 Implement sandbox disable confirmation in ConfigService
    - Add RequestSandboxDisable() method requiring Excel dialog confirmation
    - Log disable event with timestamp and Windows username
    - Keep sandbox enabled if user cancels
    - _Requirements: 3.5, 3.6_

- [x] 7. Checkpoint — Verify sandbox hardening
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Implement IPC message validation (Critical — Buffer Overflow)
  - [x] 8.1 Implement MessageValidator::ValidateFrame
    - Check buffer has at least 4 bytes for length prefix
    - Check length prefix does not exceed max_message_size (default 64 MB)
    - Check buffer contains enough data for declared length
    - Return false on any validation failure
    - _Requirements: 7.1, 7.2_

  - [x] 8.2 Implement MessageValidator::SafeUnframe with validation
    - Call ValidateFrame before attempting Protobuf deserialization
    - Attempt ParseFromArray only if frame is structurally valid
    - Log errors via LogService on failure
    - Return false without crashing on invalid data
    - _Requirements: 7.3_

  - [x] 8.3 Write property test for Protobuf Frame/Unframe round-trip
    - **Property 7: Protobuf Frame/Unframe round-trip**
    - **Validates: Requirements 7.4**
    - Test file: `tests/protobuf_ipc_pbt.cc`
    - Generator: random valid RJ2XCLBuffers::Variable messages
    - Assert: Frame() then SafeUnframe() produces equivalent message

  - [x] 8.4 Write property test for Unframe rejecting invalid data
    - **Property 8: Protobuf Unframe rejects invalid data**
    - **Validates: Requirements 7.1, 7.3**
    - Test file: `tests/protobuf_ipc_pbt.cc`
    - Generator: random byte arrays, oversized length prefixes
    - Assert: SafeUnframe returns false without crash or undefined behavior

  - [x] 8.5 Replace existing Unframe calls with SafeUnframe throughout codebase
    - Find all call sites of the existing Unframe function in pipe.cc and message_utilities.cc
    - Replace with MessageValidator::SafeUnframe
    - Ensure error handling propagates correctly at each call site
    - _Requirements: 7.1, 7.2, 7.3_

- [x] 9. Implement SafePipeHandle RAII wrapper (High — TOCTOU Race)
  - [x] 9.1 Implement SafePipeHandle with atomic read/write operations
    - Implement constructor initializing CRITICAL_SECTION
    - Implement destructor closing handle and deleting CRITICAL_SECTION
    - Implement AtomicRead: acquire CS → check validity → ReadFile → release CS
    - Implement AtomicWrite: acquire CS → check validity → WriteFile → release CS
    - Implement move semantics transferring ownership
    - _Requirements: 8.1, 8.3_

  - [x] 9.2 Implement handle invalidation and reconnection logic
    - Close() sets handle to INVALID_HANDLE_VALUE within critical section
    - On invalid handle detection: close, log error, signal reconnection needed
    - _Requirements: 8.2_

  - [x] 9.3 Replace raw HANDLE usage in pipe.cc with SafePipeHandle
    - Replace all raw HANDLE pipe variables with SafePipeHandle instances
    - Update read/write operations to use AtomicRead/AtomicWrite
    - Ensure RAII cleanup on all error paths and process termination
    - _Requirements: 8.1, 8.2, 8.3, 11.1, 11.2, 11.3_

  - [x] 9.4 Write unit tests for pipe lifecycle and handle cleanup
    - Test file: `tests/pipe_lifecycle_tests.cc`
    - Test: create pipe → connect → exchange messages → terminate → verify cleanup
    - Test: process termination closes all handles
    - Test: error during pipe creation frees partial resources
    - _Requirements: 8.1, 8.2, 11.1, 11.2, 11.3_

- [x] 10. Checkpoint — Verify IPC security
  - Ensure all tests pass, ask the user if questions arise.

- [x] 11. Add MSVC security compilation flags (High — Memory Exploits)
  - [x] 11.1 Add security flags to root CMakeLists.txt
    - Add compile options: /GS, /guard:cf, /sdl
    - Add link options: /DYNAMICBASE, /NXCOMPAT, /CETCOMPAT
    - Apply globally so all targets inherit automatically
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

  - [x] 11.2 Write build verification test for MSVC flags
    - Test file: `tests/build_verification_tests.cc`
    - Verify compiled binary has /GS, /guard:cf, /DYNAMICBASE, /NXCOMPAT via dumpbin /headers
    - _Requirements: 4.1, 4.2, 4.3_

- [x] 12. Harden GitHub Actions permissions (High — CI Compromise)
  - [x] 12.1 Add minimal permissions to build-and-test.yml
    - Add top-level `permissions: { contents: read }` declaration
    - Ensure no job has write permissions unless explicitly justified
    - _Requirements: 6.1, 6.2_

  - [x] 12.2 Write repository hygiene test for CI permissions
    - Test file: `tests/repo_hygiene_tests.cc`
    - Parse build-and-test.yml and verify permissions block exists with contents: read
    - _Requirements: 6.1_

- [x] 13. Improve .gitignore (High — Credential Leak)
  - [x] 13.1 Update .gitignore with comprehensive exclusion patterns
    - Add: Build/, node_modules/, *.pdb, __pycache__/
    - Add: neven-config.json, *.env, *.key, *.pem, crashes/
    - Verify no overlap or conflict with existing patterns
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

  - [x] 13.2 Write repository hygiene test for .gitignore patterns
    - Test file: `tests/repo_hygiene_tests.cc`
    - Verify all required patterns exist in .gitignore
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

- [x] 14. Checkpoint — Verify build and CI security
  - Ensure all tests pass, ask the user if questions arise.

- [x] 15. Eliminate eval(parse()) in R library (Medium — Code Injection)
  - [x] 15.1 Replace eval(parse()) with as.formula() in R library files
    - Scan all files in libreria/R/ for eval(parse(text=...)) patterns
    - Replace with as.formula(paste(...)) for formula construction
    - Verify no eval(parse()) remains in any production R file
    - _Requirements: 9.1, 9.2, 9.3_

  - [x] 15.2 Write verification test for eval(parse()) elimination
    - Test file: `tests/r_library_tests.cc`
    - Grep all .R files in libreria/R/ for eval(parse pattern
    - Assert zero matches
    - _Requirements: 9.2_

- [x] 16. Implement environment variable lookup with priority (Medium)
  - [x] 16.1 Implement GetNevenEnvVar with NEVEN_ > RJ2XCL_ > BERT_ fallback
    - Create or update Common/Config/EnvService with GetNevenEnvVar function
    - Priority: NEVEN_{name} → RJ2XCL_{name} → BERT_{name} → empty string
    - _Requirements: 15.2, 15.3_

  - [x] 16.2 Write property test for environment variable lookup priority
    - **Property 9: Environment variable lookup priority**
    - **Validates: Requirements 15.3**
    - Test file: `tests/env_lookup_pbt.cc`
    - Generator: random variable names + environment configurations
    - Assert: strict priority NEVEN_ > RJ2XCL_ > BERT_ > empty

- [x] 17. Remove dead code and duplicates (Medium — Attack Surface)
  - [x] 17.1 Remove dead code files and duplicates
    - Delete Console/src/shell/language_interface_julia-0.7.ts
    - Delete startup/__pycache__/ directory
    - Consolidate .neven_webview_dir() into single shared R file, remove 6 duplicates
    - Remove commented code blocks exceeding 3 lines in renderer.ts
    - _Requirements: 13.1, 13.2, 13.3, 13.4_

  - [x] 17.2 Write repository hygiene tests for dead code removal
    - Test file: `tests/repo_hygiene_tests.cc`
    - Assert language_interface_julia-0.7.ts does not exist
    - Assert __pycache__ directory does not exist
    - Assert .neven_webview_dir() defined in exactly one file
    - _Requirements: 13.1, 13.2, 13.3_

- [x] 18. Refactor Common module into subdirectories (Low — Maintainability)
  - [x] 18.1 Reorganize Common/ into subdirectories by responsibility
    - Move security files to Common/Security/ (SandboxVerifier, SecurityService, InputSanitizer)
    - Move IPC files to Common/IPC/ (pipe, message_utilities, REPLBridge, MessageValidator, SafePipeHandle)
    - Move config files to Common/Config/ (ConfigService, EnvService, NevenStartupConfig)
    - Move viewer files to Common/Viewers/ (ViewerManager, ViewerWindow, PlutoManager, etc.)
    - Move startup files to Common/Startup/ (AutoLoader, NevenInitOrchestrator, etc.)
    - Update CMakeLists.txt to reference new paths
    - Verify compilation succeeds with no API changes
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_

- [x] 19. Ensure Console independence from NEVEN_Core (Low)
  - [x] 19.1 Verify NEVEN_Core builds and functions without Console module
    - Ensure no compile-time dependency on Console/ from Core/ or Common/
    - Add conditional CMake logic to skip Console if directory absent
    - _Requirements: 2.1_

  - [x] 19.2 Write integration test for Console independence
    - Test file: `tests/integration_tests.cc`
    - Verify build completes without Console directory present
    - _Requirements: 2.1_

- [x] 20. Add Doxygen documentation to public headers (Low)
  - [x] 20.1 Add Doxygen comments to Common/ and Core/include/ public headers
    - Add @brief, @param, @return to all public functions in Common/ headers
    - Add @brief, @param, @return to all public functions in Core/include/ headers
    - Follow existing Doxygen style in the project
    - _Requirements: 14.1, 14.2, 14.3_

- [x] 21. Create naming/identity documentation (Low)
  - [x] 21.1 Create NAMING.md documenting NEVEN/RJ2XCL/BERT relationship
    - Explain historical relationship: BERT (original) → RJ2XCL (internal C++ prefix) → NEVEN (public name)
    - Document when to use each name (ABI compatibility vs user-facing vs env vars)
    - Place in docs/ directory
    - _Requirements: 15.1_

- [x] 22. Final checkpoint — Full build and test verification
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation after each severity tier
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- Build command: `cmake --build build --config Release`
- Test command: `ctest --output-on-failure -C Release --timeout 120`
- PBT library: rapidcheck integrated with Google Test v1.14.0
- All tests run without Excel, R, or Julia thanks to mock headers

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2", "1.3"] },
    { "id": 1, "tasks": ["1.4"] },
    { "id": 2, "tasks": ["2.1", "11.1", "12.1", "13.1"] },
    { "id": 3, "tasks": ["2.2", "2.3", "11.2", "12.2", "13.2"] },
    { "id": 4, "tasks": ["2.4", "2.5"] },
    { "id": 5, "tasks": ["2.6", "3.1", "3.2"] },
    { "id": 6, "tasks": ["5.1"] },
    { "id": 7, "tasks": ["5.2", "5.3", "5.4"] },
    { "id": 8, "tasks": ["5.5", "5.6", "5.8"] },
    { "id": 9, "tasks": ["5.7", "5.9", "6.1", "6.2", "6.3"] },
    { "id": 10, "tasks": ["8.1"] },
    { "id": 11, "tasks": ["8.2", "8.3"] },
    { "id": 12, "tasks": ["8.4", "8.5"] },
    { "id": 13, "tasks": ["9.1"] },
    { "id": 14, "tasks": ["9.2", "9.3"] },
    { "id": 15, "tasks": ["9.4"] },
    { "id": 16, "tasks": ["15.1", "16.1", "17.1"] },
    { "id": 17, "tasks": ["15.2", "16.2", "17.2"] },
    { "id": 18, "tasks": ["18.1"] },
    { "id": 19, "tasks": ["19.1", "20.1", "21.1"] },
    { "id": 20, "tasks": ["19.2"] }
  ]
}
```
