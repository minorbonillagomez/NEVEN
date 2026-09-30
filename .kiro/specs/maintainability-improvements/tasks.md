# Implementation Plan: Maintainability Improvements

## Overview

Conservative, behavior-preserving refactoring of the RJ2XCL C++17 codebase to raise maintainability from 5.5/10 to 8/10. Tasks are ordered from lowest-risk (constants, dead code, docs) to highest-risk (ControlBase extraction), so that each step can be validated independently against the 165-test suite. Every task ends with the codebase in a compilable, test-passing state.

## Tasks

- [x] 1. Centralize constants into `Common/Constants.h`
  - [x] 1.1 Create `Common/Constants.h` with all `inline constexpr` definitions
    - Create `RJ2XCL/Common/Constants.h` in the `rj2xcl::Constants` namespace
    - Define pipe configuration: `kPipeBufferSize` (8192), `kMaxPipeCount` (4), `kCallbackPipeIndex` (0), `kPrimaryClientPipeIndex` (1)
    - Define timeouts: `kDefaultCallTimeoutMs`, `kMaxCallTimeoutMs`, `kFileLoadingTimeoutMs`, `kFileWatchDebounceMs`, `kFileWatchNormalMs`, `kPipeRetryDelayMs`, `kMaxPipeConnectRetries`
    - Define retry limits: `kDefaultMaxRetries`, `kMaxRetriesCeiling`
    - Define buffer limits: `kMaxDynamicBufferSize`, `kStdioBufferTruncateTarget`
    - Define registry keys and environment variable names
    - Add Doxygen `/** @brief */` comments on every constant group
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.6, 5.9_

  - [x] 1.2 Replace `#define` macros and magic numbers with `Constants.h` references
    - Replace `DEFAULT_BUFFER_SIZE` and `MAX_PIPE_COUNT` in `Common/pipe.h`
    - Replace `CALLBACK_INDEX` and `PRIMARY_CLIENT_INDEX` in `ControlR/include/controlr.h`
    - Replace `kCallbackIndex`, `kPrimaryClientIndex`, `kMaxPipeCount` in `ControlPython/src/control_python.cc`
    - Replace `FILE_WATCH_LOOP_DEBOUNCE_TIMEOUT` and related macros in `RJ2XCL/include/file_change_watcher.h`
    - Replace `PIPE_BUFFER_SIZE` in `RJ2XCL/include/language_service.h`
    - Replace equivalent literals in `ControlJulia/src/control_julia.cc`
    - Remove the old `#define` macros after replacement
    - Verify each new constant value is numerically identical to the original
    - _Requirements: 2.5, 2.7_

  - [ ]* 1.3 Write unit tests for constants values
    - **Property 2: Constant Value Preservation**
    - Create `RJ2XCL/Tests/constants_tests.cc` with assertions that each constant matches its expected numeric value (e.g., `kPipeBufferSize == 8192`)
    - Add the test file to `RJ2XCL/Tests/CMakeLists.txt`
    - **Validates: Requirements 2.5**

- [x] 2. Checkpoint — Constants
  - Ensure all 165 tests pass after constants centralization, ask the user if questions arise.

- [x] 3. Remove dead code across 4 files
  - [x] 3.1 Remove dead code from `ControlJulia/src/control_julia.cc`
    - Remove commented-out `CloseClient` shutdown logic (lines 57-76)
    - Remove commented-out `ConsoleMessage` function (lines 127-131)
    - Remove commented-out `prompt_string` variable (line 133)
    - Remove commented-out active pipe stack in `Callback` (lines 553-556)
    - Remove commented-out log file initialization (line 579)
    - Verify each removed block is inside `//` or `/* */` comments — no active code removed
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.7, 4.10_

  - [x] 3.2 Remove dead code from `ControlJulia/src/julia_interface.cc`
    - Remove commented-out type introspection debug block (lines 382-427)
    - Remove commented-out debug lines (lines 57, 332, 442)
    - Verify each removed block is inside `//` or `/* */` comments
    - _Requirements: 4.5, 4.6, 4.10_

  - [x] 3.3 Remove dead code from `RJ2XCL/include/language_service.h`
    - Remove commented-out member variables (lines 95-110)
    - Verify each removed block is inside `//` or `/* */` comments
    - _Requirements: 4.8, 4.10_

  - [x] 3.4 Replace hardcoded log paths in `ControlR/src/rinterface_win.cc`
    - Replace hardcoded `C:\RJ2XCL\controlr.log` debug statements (lines 144-210) with `CHILD_LOG` macro calls
    - Include `child_log.h` if not already included
    - _Requirements: 4.9, 4.10_

- [x] 4. Checkpoint — Dead code removal
  - Ensure all 165 tests pass after dead code removal, ask the user if questions arise.
  - _Requirements: 4.11_

- [x] 5. Unify child process logging into `ChildProcessLog`
  - [x] 5.1 Create `Common/child_process_log.h` and `Common/child_process_log.cc`
    - Implement `ChildProcessLog` class with static `Initialize()`, `Shutdown()`, `Info()`, `Warn()`, `Error()`, `Debug()`, `GetFile()` methods
    - `Initialize(process_name)` opens log at `%TEMP%\control{process_name}.log`
    - Each log method prefixes with level tag (`[INFO]`, `[WARN]`, `[ERROR]`, `[DEBUG]`) and appends newline
    - `Shutdown()` flushes and closes the log file
    - If log file cannot be opened, silently discard messages without crashing
    - Update the `CHILD_LOG` / `CHILD_LOG_WARN` / `CHILD_LOG_ERR` / `CHILD_LOG_DEBUG` macros in the new header to route through `ChildProcessLog` class methods
    - Add `child_process_log.cc` to `Common/CMakeLists.txt` COMMON_SOURCES
    - _Requirements: 3.1, 3.2, 3.3, 3.6, 3.7_

  - [x] 5.2 Migrate ControlR, ControlJulia, and ControlPython to `ChildProcessLog`
    - Replace `extern FILE* g_logFile` and manual `fopen` calls in `ControlR/src/controlr.cc` with `ChildProcessLog::Initialize("controlr")`
    - Replace hardcoded `C:\RJ2XCL\controlr.log` paths with dynamic `%TEMP%` paths via `ChildProcessLog`
    - Replace `extern FILE* g_logFile` and manual `fopen` calls in `ControlJulia/src/control_julia.cc` with `ChildProcessLog::Initialize("controljulia")`
    - Replace raw `std::cout`/`std::cerr` logging in ControlJulia with `CHILD_LOG` / `CHILD_LOG_ERR` calls
    - Replace `extern FILE* g_logFile` and manual `fopen` calls in `ControlPython/src/control_python.cc` with `ChildProcessLog::Initialize("controlpython")`
    - Update `#include` directives: replace `child_log.h` with `child_process_log.h`
    - Add `ChildProcessLog::Shutdown()` calls at process exit points
    - _Requirements: 3.4, 3.5, 3.6_

  - [ ]* 5.3 Write unit tests for `ChildProcessLog`
    - **Property 5: Log Message Formatting**
    - Create `RJ2XCL/Tests/child_process_log_tests.cc`
    - Test that `Initialize()` creates a log file in `%TEMP%`
    - Test that each log level method prefixes with the correct tag and appends newline
    - Test that `Shutdown()` flushes and closes the file
    - Test that logging when file is not opened does not crash
    - Add the test file to `RJ2XCL/Tests/CMakeLists.txt`
    - **Validates: Requirements 3.1, 3.2, 3.3, 3.7**

- [x] 6. Checkpoint — ChildProcessLog
  - Ensure all 165 tests pass after logging unification, ask the user if questions arise.

- [ ] 7. Extract `ControlBase` into `Common/`
  - [ ] 7.1 Create `Common/ControlBase.h` with the abstract base class interface
    - Define the `rj2xcl::ControlBase` class with all pure virtual hooks: `OnInit`, `OnShutdown`, `OnLanguageCall`, `OnExec`, `OnShellExec`, `OnBreak`, `GetLanguageTag`, `GetDefaultPrompt`, `GetContinuationPrompt`, `OnListFunctions`, `OnReadSourceFile`
    - Define optional virtual hooks with default implementations: `OnLanguageSpecificSystemCall`, `OnParseArgs`
    - Define the `ExecResult` enum (`Complete`, `Incomplete`)
    - Declare shared infrastructure methods: `Run()`, `PushConsoleMessage()`, `ConsolePrompt()`, `Callback()`, `pipename()`
    - Declare private implementation: `PipeLoop()`, `SystemCall()`, `NextPipeInstance()`, `CloseClient()`, `QueueConsoleWrites()`, `InitLog()`, `ManagementThreadFunction()`, `StdioThreadFunction()`, `TruncateBuffer()`
    - Add full Doxygen comments on all public and protected methods
    - _Requirements: 1.1, 1.2, 1.4, 5.1_

  - [ ] 7.2 Create `Common/ControlBase.cc` with shared implementation
    - Implement `Run()`: parse `-p pipename` arg, initialize log, create pipes, call `OnInit()`, enter `PipeLoop()`, cleanup on exit
    - Return `PROCESS_ERROR_CONFIGURATION_ERROR` if `-p` argument is missing
    - Implement `PipeLoop()` with the shared message dispatch loop from the design pseudocode
    - Maintain invariant `handles.size() == pipes.size() * 2` throughout the loop
    - Implement `SystemCall()` dispatch: `get-language`, `read-source-file`, `list-functions`, `install-application-pointer`, `shutdown`, `console`, `close`
    - Route `target=system` messages to `SystemCall()` before any language-specific handler
    - Implement `NextPipeInstance()`, `CloseClient()`, `PushConsoleMessage()`, `ConsolePrompt()`, `QueueConsoleWrites()`, `TruncateBuffer()`
    - Implement `ManagementThreadFunction()` and `StdioThreadFunction()` as static thread entry points
    - Implement `Callback()` for XLL callback pipe communication
    - On `ERROR_BROKEN_PIPE`, call `CloseClient()` for that pipe index
    - On `ExecResult::Incomplete`, send continuation prompt; on `ExecResult::Complete`, clear buffer and send default prompt
    - Add `ControlBase.cc` to `Common/CMakeLists.txt` COMMON_SOURCES
    - _Requirements: 1.1, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 1.10_

  - [ ] 7.3 Refactor `ControlPython` to inherit from `ControlBase`
    - Modify `ControlPython/src/control_python.cc` to define `ControlPython : public ControlBase`
    - Override all pure virtual hooks delegating to existing `python_interface.h` functions
    - Replace `main()` with: create `ControlPython` instance, call `Run(argc, argv)`
    - Remove all duplicated functions: `GetLastErrorAsString`, `NextPipeInstance`, `CloseClient`, `PushConsoleMessage`, `ConsolePrompt`, `QueueConsoleWrites`, `TruncateBuffer`, `StdioThreadFunction`, `ManagementThreadFunction`, `pipe_loop`, shared `SystemCall` logic
    - Update `ControlPython/CMakeLists.txt` to link against `Common` library
    - _Requirements: 1.1, 1.2, 1.3_

  - [ ] 7.4 Refactor `ControlJulia` to inherit from `ControlBase`
    - Modify `ControlJulia/src/control_julia.cc` to define `ControlJulia : public ControlBase`
    - Override all pure virtual hooks delegating to existing `julia_interface.h` functions
    - Replace `main()` with: create `ControlJulia` instance, call `Run(argc, argv)`
    - Remove all duplicated functions (same list as 7.3)
    - Handle Julia-specific differences (e.g., UV loop idle tick, Julia GC integration)
    - Update `ControlJulia/CMakeLists.txt` to link against `Common` library
    - _Requirements: 1.1, 1.2, 1.3_

  - [ ] 7.5 Refactor `ControlR` to inherit from `ControlBase`
    - Modify `ControlR/src/controlr.cc` to define `ControlR : public ControlBase`
    - Override all pure virtual hooks delegating to existing R interface functions
    - Replace `main()` / `InputStreamRead()` with: create `ControlR` instance, call `Run(argc, argv)`
    - Remove all duplicated functions (same list as 7.3)
    - Handle R-specific differences (e.g., R event loop integration, `InputStreamRead` pattern)
    - Update `ControlR/CMakeLists.txt` to link against `Common` library
    - _Requirements: 1.1, 1.2, 1.3_

  - [ ]* 7.6 Write property tests for `ControlBase::SystemCall` dispatch
    - **Property 4: System Call Dispatch Priority**
    - Create test in `RJ2XCL/Tests/control_base_tests.cc`
    - Create a mock `ControlBase` subclass that records which virtual hooks are called
    - Test that for any `CallResponse` with `target=system`, the message is routed to `SystemCall()` and never to `OnLanguageCall`, `OnExec`, or `OnShellExec`
    - Test dispatch for each system command: `get-language`, `read-source-file`, `list-functions`, `shutdown`, `console`, `close`
    - Add the test file to `RJ2XCL/Tests/CMakeLists.txt`
    - **Validates: Requirements 1.8**

  - [ ]* 7.7 Write property test for pipe loop invariant
    - **Property 3: Pipe Loop Invariant**
    - Add test to `RJ2XCL/Tests/control_base_tests.cc`
    - Verify that after pipe connect, disconnect, and reconnect sequences, `handles.size() == pipes.size() * 2` holds
    - **Validates: Requirements 1.6**

- [ ] 8. Checkpoint — ControlBase extraction
  - Ensure all 165 tests pass after ControlBase extraction, ask the user if questions arise.
  - _Requirements: 6.1_

- [x] 9. Add inline Doxygen documentation to key classes
  - [x] 9.1 Add Doxygen comments to `ConfigService`, `LanguageService`, and `LanguageManager`
    - Add `/** @brief ... */` comments to every public method of `ConfigService` in `Common/ConfigService.h`
    - Add `/** @brief ... */` comments to every public method of `LanguageService` in `RJ2XCL/include/language_service.h`
    - Add `/** @brief ... */` comments to every public method of `LanguageManager` (locate header in `RJ2XCL/include/`)
    - Include `@param` and `@return` tags for methods with parameters or non-void return types
    - _Requirements: 5.2, 5.3, 5.4, 5.10_

  - [x] 9.2 Add Doxygen comments to `DiscoveryService`, `SecurityService`, `SandboxVerifier`, and `LogService`
    - Add `/** @brief ... */` comments to every public method of `DiscoveryService` in `Common/DiscoveryService.h`
    - Add `/** @brief ... */` comments to every public method of `SecurityService` in `Common/SecurityService.h`
    - Add `/** @brief ... */` comments to every public method of `SandboxVerifier` (locate header or check if methods are declared in `.cc`)
    - Add `/** @brief ... */` comments to every public method of `LogService` in `Common/LogService.h`
    - Include `@param` and `@return` tags for methods with parameters or non-void return types
    - _Requirements: 5.5, 5.6, 5.7, 5.8, 5.10_

- [x] 10. Final checkpoint — Full regression
  - Ensure all 165 tests pass with zero failures and zero test modifications, ask the user if questions arise.
  - Verify no new external dependencies were introduced beyond C++17 stdlib, Windows API, Protobuf, and Google Test
  - Verify no security-sensitive code paths were modified (`SandboxVerifier`, `SecurityService`, `ConfigService::ValidateConfig()`)
  - _Requirements: 6.1, 6.3, 6.4, 6.5_

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Tasks are ordered lowest-risk first: constants (1) → dead code (3) → logging (5) → ControlBase (7) → docs (9)
- Each checkpoint verifies the full 165-test suite passes before proceeding to the next phase
- Property tests validate the correctness properties defined in the design document
- ControlPython is refactored first (task 7.3) because it has the simplest language interface, making it the safest pilot for the ControlBase pattern
- No behavioral changes are introduced — all refactoring is structural only
