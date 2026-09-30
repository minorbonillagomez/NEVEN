# Requirements Document

## Introduction

This document formalizes the requirements for the RJ2XCL maintainability improvements. The project currently has significant code duplication across three ControlX child processes (~400 lines each), scattered constant definitions, inconsistent child process logging, ~110 lines of dead code, and insufficient inline documentation. These requirements derive from the approved design document and target raising the maintainability score from 5.5/10 to 8/10 through conservative, behavior-preserving refactoring.

## Glossary

- **ControlBase**: Abstract C++ base class in `Common/` that encapsulates shared pipe management, message dispatch, management thread, stdio thread, and console buffering logic.
- **ControlX**: Collective term for the three child process executables: ControlR, ControlJulia, and ControlPython.
- **Constants**: A centralized C++ header (`Constants.h`) providing `inline constexpr` definitions for all numeric constants, timeouts, buffer sizes, and pipe indices.
- **ChildProcessLog**: A unified logging facility class that replaces the current mix of `std::cout`, `std::cerr`, hardcoded log paths, and inconsistent `g_logFile` management across child processes.
- **Dead_Code**: Lines of source code that are commented out (`//`, `/* */`, `#if 0`) or unreachable, providing no runtime behavior.
- **Doxygen_Comment**: A documentation comment following the `/** @brief ... */` format, suitable for automated documentation generation.
- **Pipe**: Named Pipe IPC channel between the XLL process and a ControlX child process.
- **Protobuf_Message**: A Protocol Buffers serialized message (`CallResponse`) used for IPC between XLL and ControlX processes.
- **XLL**: The Excel add-in (rj2xcl.xll) that runs inside the Excel process.
- **Test_Suite**: The existing 165-test Google Test suite that validates system behavior.
- **Virtual_Hook**: A pure virtual method in ControlBase that subclasses override to provide language-specific behavior.
- **System_Call**: A function call with `target=system` in the Protobuf message, dispatched by ControlBase to shared handlers.

## Requirements

### Requirement 1: ControlBase Extraction

**User Story:** As a maintainer, I want the shared pipe management, message dispatch, and thread infrastructure extracted into a single ControlBase class, so that bug fixes and improvements apply to all three language processes without tripling the effort.

#### Acceptance Criteria

1. THE Build_System SHALL compile a `ControlBase` class located in `Common/` that is linked by ControlR, ControlJulia, and ControlPython targets.
2. WHEN a ControlX subclass is compiled, THE Compiler SHALL enforce that all pure virtual hooks (`OnInit`, `OnShutdown`, `OnLanguageCall`, `OnExec`, `OnShellExec`, `OnBreak`, `GetLanguageTag`, `GetDefaultPrompt`, `GetContinuationPrompt`, `OnListFunctions`, `OnReadSourceFile`) are overridden.
3. WHEN a valid Protobuf message is sent to any ControlX process, THE ControlBase SHALL produce a byte-identical response compared to the pre-refactoring implementation for the same input.
4. THE ControlBase SHALL contain exactly one implementation of each of the following functions: `GetLastErrorAsString`, `NextPipeInstance`, `PushConsoleMessage`, `ConsolePrompt`, `QueueConsoleWrites`, `TruncateBuffer`, `StdioThreadFunction`, and `ManagementThreadFunction`.
5. WHEN ControlBase::Run() is called without a `-p pipename` argument, THE ControlBase SHALL return `PROCESS_ERROR_CONFIGURATION_ERROR`.
6. WHEN ControlBase::PipeLoop() is running, THE ControlBase SHALL maintain the invariant that `handles.size() == pipes.size() * 2`.
7. WHEN a pipe read returns `ERROR_BROKEN_PIPE`, THE ControlBase SHALL call `CloseClient()` for that pipe index and make the slot available for reconnection.
8. WHEN a `kFunctionCall` message with `target=system` is received, THE ControlBase SHALL dispatch it to `SystemCall()` before considering language-specific handlers.
9. WHEN a `kShellCommand` message completes with `ExecResult::Incomplete`, THE ControlBase SHALL send a continuation prompt via `ConsolePrompt()`.
10. WHEN a `kShellCommand` message completes with `ExecResult::Complete`, THE ControlBase SHALL clear the shell buffer and send the default prompt via `ConsolePrompt()`.

### Requirement 2: Constants Centralization

**User Story:** As a maintainer, I want all numeric constants, timeouts, buffer sizes, and pipe indices defined in a single `Constants.h` header, so that I can find and update configuration values in one place instead of searching across six files.

#### Acceptance Criteria

1. THE Constants header SHALL define all pipe configuration values (`kPipeBufferSize`, `kMaxPipeCount`, `kCallbackPipeIndex`, `kPrimaryClientPipeIndex`) as `inline constexpr` values in the `rj2xcl::Constants` namespace.
2. THE Constants header SHALL define all timeout values (`kDefaultCallTimeoutMs`, `kMaxCallTimeoutMs`, `kFileLoadingTimeoutMs`, `kFileWatchDebounceMs`, `kFileWatchNormalMs`, `kPipeRetryDelayMs`) as `inline constexpr` values.
3. THE Constants header SHALL define all retry limits (`kDefaultMaxRetries`, `kMaxRetriesCeiling`, `kMaxPipeConnectRetries`) as `inline constexpr` values.
4. THE Constants header SHALL define all buffer limits (`kMaxDynamicBufferSize`, `kStdioBufferTruncateTarget`) as `inline constexpr` values.
5. WHEN a constant in `Constants.h` replaces a `#define` macro, THE Constants value SHALL be numerically identical to the original macro value it replaces.
6. WHEN `Constants.h` is included, THE Constants header SHALL not introduce any `#define` macros into the global namespace.
7. THE Build_System SHALL compile successfully after all original `#define` macros for constants (`DEFAULT_BUFFER_SIZE`, `MAX_PIPE_COUNT`, `CALLBACK_INDEX`, `PRIMARY_CLIENT_INDEX`, `PIPE_BUFFER_SIZE`, `FILE_WATCH_LOOP_DEBOUNCE_TIMEOUT`) are removed from their original files and replaced with references to `Constants.h`.

### Requirement 3: ChildProcessLog Unification

**User Story:** As a maintainer, I want a unified logging facility for all child processes, so that log output is consistent in format, location, and behavior regardless of which language process generates it.

#### Acceptance Criteria

1. WHEN `ChildProcessLog::Initialize()` is called with a process name, THE ChildProcessLog SHALL create a log file at `%TEMP%\control{process_name}.log`.
2. WHEN a log message is written via `ChildProcessLog::Info()`, `Warn()`, `Error()`, or `Debug()`, THE ChildProcessLog SHALL prefix the message with the corresponding level tag (`[INFO]`, `[WARN]`, `[ERROR]`, `[DEBUG]`) and append a newline.
3. WHEN `ChildProcessLog::Shutdown()` is called, THE ChildProcessLog SHALL flush and close the log file.
4. THE ChildProcessLog SHALL replace all hardcoded `C:\RJ2XCL\*.log` paths in ControlR, ControlJulia, and ControlPython with dynamic `%TEMP%`-based paths.
5. THE ChildProcessLog SHALL replace all raw `std::cout` and `std::cerr` logging statements in ControlJulia with calls to the unified logging API.
6. WHEN the `CHILD_LOG`, `CHILD_LOG_WARN`, `CHILD_LOG_ERR`, or `CHILD_LOG_DEBUG` macros are used, THE ChildProcessLog SHALL route them through the `ChildProcessLog` class methods while maintaining the same call-site syntax.
7. IF the log file cannot be opened, THEN THE ChildProcessLog SHALL silently discard log messages without crashing the process.

### Requirement 4: Dead Code Removal

**User Story:** As a maintainer, I want all commented-out and unreachable code removed from the codebase, so that the source files contain only active, relevant code and are easier to read and navigate.

#### Acceptance Criteria

1. THE Refactoring SHALL remove the commented-out `CloseClient` shutdown logic in `control_julia.cc` (lines 57-76).
2. THE Refactoring SHALL remove the commented-out `ConsoleMessage` function in `control_julia.cc` (lines 127-131).
3. THE Refactoring SHALL remove the commented-out `prompt_string` variable in `control_julia.cc` (line 133).
4. THE Refactoring SHALL remove the commented-out active pipe stack in `control_julia.cc` `Callback` function (lines 553-556).
5. THE Refactoring SHALL remove the commented-out type introspection debug block in `julia_interface.cc` (lines 382-427).
6. THE Refactoring SHALL remove the commented-out debug lines in `julia_interface.cc` (lines 57, 332, 442).
7. THE Refactoring SHALL remove the commented-out log file initialization in `control_julia.cc` (line 579).
8. THE Refactoring SHALL remove the commented-out member variables in `language_service.h` (lines 95-110).
9. THE Refactoring SHALL replace the hardcoded `C:\RJ2XCL\controlr.log` debug statements in `rinterface_win.cc` (lines 144-210) with `CHILD_LOG` macro calls.
10. WHEN any line is removed as dead code, THE Refactoring SHALL verify that the line is inside a block comment (`/* ... */`), preceded by `//`, or inside an `#if 0` block — no active code is removed.
11. WHEN all dead code removal is complete, THE Test_Suite SHALL pass all 165 tests with zero failures.

### Requirement 5: Inline Documentation

**User Story:** As a maintainer, I want Doxygen-style comments on all public methods of key classes, so that any developer can understand the purpose, parameters, and behavior of each method without reading the implementation.

#### Acceptance Criteria

1. WHEN the documentation pass is complete, THE Codebase SHALL have a `/** @brief ... */` Doxygen comment on every public method of `ControlBase`.
2. WHEN the documentation pass is complete, THE Codebase SHALL have a `/** @brief ... */` Doxygen comment on every public method of `ConfigService`.
3. WHEN the documentation pass is complete, THE Codebase SHALL have a `/** @brief ... */` Doxygen comment on every public method of `LanguageService`.
4. WHEN the documentation pass is complete, THE Codebase SHALL have a `/** @brief ... */` Doxygen comment on every public method of `LanguageManager`.
5. WHEN the documentation pass is complete, THE Codebase SHALL have a `/** @brief ... */` Doxygen comment on every public method of `DiscoveryService`.
6. WHEN the documentation pass is complete, THE Codebase SHALL have a `/** @brief ... */` Doxygen comment on every public method of `SecurityService`.
7. WHEN the documentation pass is complete, THE Codebase SHALL have a `/** @brief ... */` Doxygen comment on every public method of `SandboxVerifier`.
8. WHEN the documentation pass is complete, THE Codebase SHALL have a `/** @brief ... */` Doxygen comment on every public method of `LogService`.
9. WHEN the documentation pass is complete, THE Codebase SHALL have a `/** @brief ... */` Doxygen comment on every constant group in `Constants.h`.
10. THE Doxygen_Comments SHALL include at minimum a `@brief` description; `@param` and `@return` tags SHALL be included for methods with parameters or non-void return types.

### Requirement 6: Behavioral Preservation

**User Story:** As a user of RJ2XCL, I want the refactoring to produce zero behavioral changes, so that all my existing Excel formulas, scripts, and workflows continue to work identically.

#### Acceptance Criteria

1. WHEN the full refactoring is complete, THE Test_Suite SHALL pass all 165 existing tests with zero failures and zero test modifications.
2. WHEN a valid Protobuf message is sent to any ControlX process after refactoring, THE ControlX process SHALL produce a response identical to the pre-refactoring response for the same input.
3. THE Refactoring SHALL not modify any security-sensitive code paths in `SandboxVerifier`, `SecurityService`, or `ConfigService::ValidateConfig()`.
4. THE Refactoring SHALL not introduce any new external dependencies beyond C++17 standard library, Windows API, Google Protobuf, and Google Test.
5. THE Refactoring SHALL not introduce any new threads, synchronization primitives, or heap allocations beyond those in the pre-refactoring code.
6. WHEN `ControlBase` dispatches a message via virtual hooks, THE virtual call overhead SHALL be negligible relative to the pipe round-trip latency (virtual call adds ~2-5 nanoseconds vs microsecond-to-millisecond pipe latency).
