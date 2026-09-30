# Requirements Document

## Introduction

This document specifies reliability improvements for the RJ2XCL Excel add-in (XLL) that integrates R, Julia, and Python via Named Pipes and Protobuf. The current reliability score is 6/10. These requirements target raising it to 7.5–8/10 through surgical, low-risk changes: defensive validation, user-facing error messages, diagnostics logging, configurable timeouts, and process health checks. No architectural rewrites, no new threads, no pipe protocol changes. All 165 existing tests must continue to pass.

## Glossary

- **XLL**: The RJ2XCL Excel add-in DLL loaded by Microsoft Excel.
- **LanguageService**: The C++ class (`language_service.cc`) that manages the lifecycle and IPC communication with a single child language process (R, Julia, or Python).
- **LanguageManager**: The singleton registry (`LanguageManager.cc`) that owns all LanguageService instances and dispatches calls.
- **ControlX_Process**: A child process (ControlR.exe, ControlJulia.exe, or ControlPython.exe) that hosts a language runtime and communicates with the XLL via Named Pipes.
- **Named_Pipe**: A Windows IPC mechanism used for bidirectional communication between the XLL and each ControlX_Process.
- **Pipe_Handle**: The Windows HANDLE returned by `CreateFileA` for the Named Pipe connection to a ControlX_Process.
- **Call_Method**: The `LanguageService::Call()` function — the core IPC entry point that serializes a Protobuf request, writes it to the Named_Pipe, and reads the response.
- **ConfigService**: The singleton (`ConfigService.cc`) that reads `rj2xcl-config.json` and exposes typed getters for timeouts, retries, and feature flags.
- **LogService**: The thread-safe singleton (`LogService.cc`) that writes timestamped, severity-tagged messages to a log file via `RJ2XCL_LOG_*` macros.
- **Protobuf_Message**: A serialized Protocol Buffer message (`CallResponse`) used for all XLL ↔ ControlX_Process communication.
- **Graceful_Degradation**: The ability of the XLL to continue serving requests for healthy languages when one or more ControlX_Processes have failed.
- **Health_Status**: A per-language enumeration (Healthy, Unavailable, Unknown) indicating whether a ControlX_Process is alive and responsive.

## Requirements

### Requirement 1: Graceful Degradation When a Language Fails

**User Story:** As an Excel user, I want R and Julia to continue working when Python crashes, so that a single language failure does not block my entire workflow.

#### Acceptance Criteria

1. WHEN a ControlX_Process terminates unexpectedly, THE LanguageManager SHALL continue dispatching calls to other LanguageService instances that remain connected.
2. WHEN a call is dispatched to a LanguageService whose ControlX_Process has terminated, THE LanguageService SHALL return a descriptive error message in the Protobuf_Message response without throwing an exception or hanging.
3. IF a ControlX_Process terminates while a Call_Method is waiting for a response, THEN THE LanguageService SHALL detect the broken Named_Pipe within the configured timeout and return an error message identifying the failed language by name.
4. WHEN a LanguageService detects that its ControlX_Process has terminated, THE LanguageService SHALL set its connected status to false and log the event at ERROR level via LogService.
5. THE LanguageManager SHALL NOT shut down or restart healthy LanguageService instances when an unrelated ControlX_Process fails.

### Requirement 2: User-Friendly Error Messages

**User Story:** As an Excel user, I want clear error messages when a language service is unavailable, so that I understand what happened and what to do next.

#### Acceptance Criteria

1. WHEN a Named_Pipe write fails with ERROR_BROKEN_PIPE, THE LanguageService SHALL return the error message: "[Language] service unavailable — restart Excel to reconnect." where [Language] is the display name of the failed language (R, Julia, or Python).
2. WHEN a Named_Pipe read times out, THE LanguageService SHALL return the error message: "[Language] did not respond within [N] seconds. Check the log file for details." where [Language] is the display name and [N] is the configured timeout in seconds.
3. WHEN reconnection fails after the maximum retry count, THE LanguageService SHALL return the error message: "[Language] reconnection failed after [N] attempts — restart Excel." where [N] is the configured maximum retry count.
4. WHEN a ControlX_Process exits with a non-zero exit code during connection, THE LanguageService SHALL return the error message: "[Language] process exited unexpectedly (code [X]). Check the log file." where [X] is the numeric exit code.
5. THE LanguageService SHALL include the language display name in every error message returned to the user via the Protobuf_Message err field.

### Requirement 3: Pipe State Validation Before Operations

**User Story:** As a developer, I want the pipe handle validated before every read/write operation, so that stale handles do not cause crashes.

#### Acceptance Criteria

1. WHEN the Call_Method is invoked, THE LanguageService SHALL verify that the Pipe_Handle is valid (not INVALID_HANDLE_VALUE and not null) before calling WriteFile.
2. IF the Pipe_Handle is invalid at the start of a Call_Method invocation, THEN THE LanguageService SHALL return an error message indicating the pipe is not connected, without attempting a WriteFile call.
3. WHEN the connected status is true but the Pipe_Handle is invalid, THE LanguageService SHALL set connected status to false and log a warning via LogService before returning the error.
4. THE LanguageService SHALL validate the Pipe_Handle before each ReadFile call within the response-reading loop of the Call_Method.
5. IF the Pipe_Handle becomes invalid during the response-reading loop, THEN THE LanguageService SHALL break out of the loop and return a pipe-state error message instead of attempting further reads.

### Requirement 4: Configurable Timeout Per Language

**User Story:** As a system administrator, I want to configure different call timeouts for each language (Julia needs longer for JIT, Python needs shorter), so that each language has an appropriate timeout.

#### Acceptance Criteria

1. THE ConfigService SHALL read a per-language `callTimeoutMs` value from the `rj2xcl-config.json` configuration file under each language section (e.g., `RJ2XCL.Julia.callTimeoutMs`).
2. WHEN a per-language `callTimeoutMs` is specified, THE LanguageService SHALL use that value instead of the global `callTimeoutMs` for the Call_Method timeout.
3. WHEN a per-language `callTimeoutMs` is not specified, THE LanguageService SHALL fall back to the global `callTimeoutMs` value from ConfigService.
4. THE ConfigService SHALL validate that per-language `callTimeoutMs` values are within the range 1000–1800000 milliseconds and log a warning if out of range.
5. THE ConfigService SHALL clamp out-of-range per-language `callTimeoutMs` values to the nearest valid bound (1000 ms minimum, 1800000 ms maximum) rather than rejecting them.

### Requirement 5: Reconnection Logging and Diagnostics

**User Story:** As a developer debugging a production issue, I want detailed logs when reconnection happens, so that I can diagnose pipe failures and process crashes.

#### Acceptance Criteria

1. WHEN the Call_Method initiates a reconnection attempt, THE LanguageService SHALL log at INFO level: the language name, the pipe name, the retry attempt number, and the reason for reconnection (e.g., ERROR_BROKEN_PIPE, ERROR_NO_DATA).
2. WHEN a reconnection attempt succeeds, THE LanguageService SHALL log at INFO level: the language name, the pipe name, and the total elapsed time of the reconnection.
3. WHEN a reconnection attempt fails, THE LanguageService SHALL log at ERROR level: the language name, the pipe name, the Windows error code, and the retry attempt number.
4. WHEN the maximum retry count is exceeded, THE LanguageService SHALL log at ERROR level: the language name, the total number of attempts, and the original error that triggered reconnection.
5. WHEN a ControlX_Process exit code is retrieved during reconnection, THE LanguageService SHALL log the exit code at WARNING level with the language name.

### Requirement 6: Process Health Monitoring

**User Story:** As an Excel user, I want the add-in to detect when a language process has died, so that subsequent calls fail fast with a clear message instead of hanging until timeout.

#### Acceptance Criteria

1. WHEN the Call_Method is invoked, THE LanguageService SHALL check whether the ControlX_Process is still alive (via `GetExitCodeProcess`) before writing to the Named_Pipe.
2. IF the ControlX_Process has exited, THEN THE LanguageService SHALL set connected status to false, log the exit code at ERROR level, and return an error message: "[Language] process is not running (exit code [X])." without attempting pipe I/O.
3. WHEN the ControlX_Process is detected as exited during a health check, THE LanguageService SHALL store the Health_Status as Unavailable for that language.
4. THE LanguageService SHALL expose a method to query the current Health_Status of its ControlX_Process.
5. WHEN a LanguageService Health_Status is Unavailable, THE LanguageManager SHALL skip dispatching calls to that service and return an error message: "[Language] is currently unavailable." directly.
