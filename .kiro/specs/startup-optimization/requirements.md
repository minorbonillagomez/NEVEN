# Requirements Document: Startup Optimization

## Introduction

This feature redesigns the NEVEN XLL initialization sequence to prevent Excel from hanging or freezing during load. The current `Init()` method executes all language engine connections, startup scripts, and user file loading sequentially on Excel's main UI thread, causing freezes of 10–30+ seconds. The optimized startup moves blocking operations to background threads, enabling Excel to become responsive within 3 seconds while language engines connect and initialize progressively.

The design targets world-class reliability: zero-freeze startup, full observability, graceful degradation, and progressive enhancement — ensuring that NEVEN feels instantaneous regardless of how many languages or user files are configured.

## Glossary

- **XLL**: Excel Add-in Library — a DLL loaded by Excel at startup via `xlAutoOpen`.
- **Init_Orchestrator**: The component responsible for coordinating the startup sequence, replacing the current monolithic `Init()` method.
- **Language_Engine**: A child process (ControlR.exe, ControlJulia.exe, or ControlPython.exe) that embeds a scripting runtime and communicates via Named Pipes.
- **Pipe_Connection_Loop**: The retry loop that attempts to connect to a Language_Engine's Named Pipe (up to configurable retries with exponential backoff).
- **Background_Connector**: A worker thread responsible for connecting Language_Engines without blocking the UI thread.
- **Progressive_Registration**: The mechanism by which Excel functions become available incrementally as each Language_Engine completes initialization.
- **Startup_Script**: Language-specific initialization code sent to a Language_Engine after pipe connection (e.g., R startup, Python startup.py).
- **User_Function_File**: A script file (.R, .jl, .py) in the user's `Documents/NEVEN/functions/` directory loaded at startup.
- **Health_Status**: An enum tracking the state of a Language_Engine (Pending, Connecting, Healthy, Degraded, Unavailable).
- **UI_Thread**: Excel's main application thread — blocking this thread freezes the Excel interface.
- **Deferred_Init_Queue**: A thread-safe queue of initialization tasks to be executed on background threads.
- **Startup_Telemetry**: Timing and status data collected during initialization for diagnostics and performance monitoring.
- **Status_Bar_Reporter**: Component that communicates startup progress to the user via Excel's status bar.
- **Startup_Phase**: A discrete stage of initialization (Configure, Connect, Initialize, LoadFiles, Register).
- **Watchdog_Timer**: A safety mechanism that detects and terminates stuck initialization tasks.

## Requirements

### Requirement 1: Non-Blocking Init Entry Point

**User Story:** As an Excel user, I want the XLL to load without freezing Excel, so that I can begin working immediately while language engines start in the background.

#### Acceptance Criteria

1. WHEN Excel calls `xlAutoOpen`, THE Init_Orchestrator SHALL complete its UI-thread work and return control to Excel within 3 seconds.
2. THE Init_Orchestrator SHALL execute only non-blocking operations on the UI_Thread: configuration reading, JobObject creation, and basic function registration.
3. WHEN the Init_Orchestrator returns control to Excel, THE Init_Orchestrator SHALL have dispatched all Language_Engine connection tasks to the Background_Connector.
4. THE Init_Orchestrator SHALL register placeholder functions for all configured languages before returning control to Excel, so that the function wizard shows expected entries.
5. THE Init_Orchestrator SHALL separate the startup sequence into distinct Startup_Phases: Configure, Connect, Initialize, LoadFiles, Register.
6. WHEN the Init_Orchestrator begins background initialization, THE Init_Orchestrator SHALL set a global initialization state flag that other components can query.

### Requirement 2: Parallel Language Engine Connection

**User Story:** As an Excel user, I want all language engines to connect simultaneously, so that total startup time is bounded by the slowest engine rather than the sum of all engines.

#### Acceptance Criteria

1. THE Background_Connector SHALL launch connection attempts for all configured Language_Engines concurrently using separate threads.
2. WHEN a Language_Engine's Pipe_Connection_Loop succeeds, THE Background_Connector SHALL update that engine's Health_Status to Healthy.
3. IF a Language_Engine's Pipe_Connection_Loop exhausts all retries without connecting, THEN THE Background_Connector SHALL set that engine's Health_Status to Unavailable and log a warning with the total elapsed time.
4. IF a Language_Engine's child process exits prematurely during connection, THEN THE Background_Connector SHALL immediately abort the Pipe_Connection_Loop for that engine, set Health_Status to Unavailable, and record the exit code.
5. WHILE the Background_Connector is connecting Language_Engines, THE UI_Thread SHALL remain responsive to user interaction.
6. THE Background_Connector SHALL use exponential backoff for pipe connection retries (starting at 50ms, doubling up to 800ms, with a total timeout of 15 seconds per engine).
7. THE Background_Connector SHALL prioritize Language_Engine connection order based on historical startup speed (fastest engine first) to maximize early function availability.

### Requirement 3: Background Startup Script Execution

**User Story:** As an Excel user, I want startup scripts to execute without blocking Excel, so that heavy initialization (Python imports, R library loading) happens transparently.

#### Acceptance Criteria

1. WHEN a Language_Engine reaches Healthy status, THE Background_Connector SHALL send the Startup_Script for that engine on the background thread.
2. WHILE a Startup_Script is executing, THE UI_Thread SHALL remain responsive.
3. WHEN a Startup_Script completes successfully, THE Init_Orchestrator SHALL trigger Progressive_Registration for that Language_Engine's functions.
4. IF a Startup_Script fails or times out after 30 seconds, THEN THE Init_Orchestrator SHALL set the Language_Engine's Health_Status to Degraded and log the failure with diagnostic details.
5. THE Init_Orchestrator SHALL record the execution time of each Startup_Script in Startup_Telemetry.

### Requirement 4: Asynchronous User Function File Loading

**User Story:** As an Excel user with many custom function files, I want my files to load in the background, so that a single slow file does not freeze Excel.

#### Acceptance Criteria

1. THE Init_Orchestrator SHALL load User_Function_Files on background threads, not on the UI_Thread.
2. WHEN a User_Function_File is loaded successfully, THE Init_Orchestrator SHALL trigger Progressive_Registration to make the new functions available in Excel.
3. IF a User_Function_File times out after 30 seconds, THEN THE Init_Orchestrator SHALL skip that file, log a warning including the file name and language, and continue loading remaining files.
4. THE Init_Orchestrator SHALL load User_Function_Files for each Language_Engine only after that engine's Startup_Script has completed.
5. WHILE User_Function_Files are loading, THE UI_Thread SHALL remain responsive.
6. THE Init_Orchestrator SHALL load User_Function_Files in parallel across different Language_Engines (R files and Julia files load concurrently).
7. IF a User_Function_File causes a Language_Engine to crash, THEN THE Init_Orchestrator SHALL detect the crash, mark the engine as Unavailable, and skip remaining files for that engine.

### Requirement 5: Progressive Function Registration

**User Story:** As an Excel user, I want functions to become available as each language engine finishes initializing, so that I can start using R functions even if Julia is still loading.

#### Acceptance Criteria

1. WHEN a Language_Engine completes initialization and function discovery, THE Init_Orchestrator SHALL register that engine's functions with Excel via `xlfRegister`.
2. THE Init_Orchestrator SHALL call `xlfRegister` on the UI_Thread using Excel's `xlcOnTime` scheduling mechanism to avoid COM threading violations.
3. WHEN new functions are registered progressively, THE Init_Orchestrator SHALL not re-register functions that are already registered.
4. THE Init_Orchestrator SHALL complete all Progressive_Registration within 60 seconds of XLL load for a system with all engines healthy.
5. WHEN Progressive_Registration completes for a Language_Engine, THE Init_Orchestrator SHALL update the Status_Bar_Reporter with the count of newly available functions.

### Requirement 6: Startup Health Reporting

**User Story:** As an Excel user, I want to know which language engines are available, so that I can understand why certain functions may not work yet.

#### Acceptance Criteria

1. THE Init_Orchestrator SHALL expose the Health_Status of each configured Language_Engine through a queryable interface.
2. WHEN a user calls a function whose Language_Engine has Health_Status of Connecting, THE Init_Orchestrator SHALL return a descriptive message indicating the engine is still starting, including estimated time remaining if available.
3. WHEN a user calls a function whose Language_Engine has Health_Status of Unavailable, THE Init_Orchestrator SHALL return a descriptive error message indicating the engine failed to connect and suggest troubleshooting steps.
4. WHEN all Language_Engines have completed connection attempts (Healthy or Unavailable), THE Init_Orchestrator SHALL log a summary of startup results including elapsed time per engine and total startup duration.
5. THE Init_Orchestrator SHALL provide a `NEVEN.STATUS()` Excel function that returns a formatted summary of all engine states and startup timing.

### Requirement 7: Thread Safety During Initialization

**User Story:** As a developer, I want the concurrent initialization to be thread-safe, so that race conditions do not cause crashes or data corruption.

#### Acceptance Criteria

1. THE Background_Connector SHALL use synchronization primitives to protect shared state (language_services_ vector, Health_Status fields) from concurrent access.
2. WHEN the UI_Thread reads Health_Status while the Background_Connector is writing it, THE Init_Orchestrator SHALL guarantee no data races occur.
3. THE Init_Orchestrator SHALL ensure that `xlfRegister` calls are serialized on the UI_Thread, even when multiple Background_Connector threads complete simultaneously.
4. IF the XLL is unloaded (xlAutoClose) while background initialization is in progress, THEN THE Init_Orchestrator SHALL signal all background threads to terminate and wait for completion with a 5-second timeout before releasing resources.
5. THE Init_Orchestrator SHALL use RAII-based lock management to prevent deadlocks during initialization.
6. THE Background_Connector SHALL not hold locks while performing blocking I/O operations (pipe connection, process launch).

### Requirement 8: Graceful Degradation

**User Story:** As an Excel user, I want Excel to remain functional even if one or more language engines fail to start, so that a broken Julia installation does not prevent me from using R functions.

#### Acceptance Criteria

1. IF one Language_Engine fails to connect, THEN THE Init_Orchestrator SHALL continue initialization of all other Language_Engines without interruption.
2. WHEN a Language_Engine is Unavailable, THE Init_Orchestrator SHALL register that engine's functions as stubs that return a descriptive error message when called.
3. THE Init_Orchestrator SHALL not retry a failed Language_Engine connection automatically during the same Excel session unless explicitly requested by the user.
4. IF all Language_Engines fail to connect, THEN THE Init_Orchestrator SHALL still complete startup successfully with basic XLL functions (help, version, status) available.
5. IF a Language_Engine transitions from Healthy to Unavailable during file loading (crash), THEN THE Init_Orchestrator SHALL preserve all previously registered functions from that engine as stubs.

### Requirement 9: Startup Progress Feedback

**User Story:** As an Excel user, I want visual feedback during startup, so that I know NEVEN is loading and can estimate when it will be ready.

#### Acceptance Criteria

1. WHILE background initialization is in progress, THE Status_Bar_Reporter SHALL display progress messages in Excel's status bar indicating the current Startup_Phase.
2. WHEN a Language_Engine transitions to Healthy, THE Status_Bar_Reporter SHALL display a message confirming that engine is ready (e.g., "NEVEN: R ready ✓").
3. WHEN all initialization is complete, THE Status_Bar_Reporter SHALL display a final summary message and clear it after 5 seconds.
4. THE Status_Bar_Reporter SHALL update the status bar at most once per second to avoid flickering.
5. IF initialization takes longer than 10 seconds, THEN THE Status_Bar_Reporter SHALL include elapsed time in the status message.

### Requirement 10: Startup Telemetry and Diagnostics

**User Story:** As a developer or support engineer, I want detailed timing data from each startup, so that I can identify bottlenecks and regressions.

#### Acceptance Criteria

1. THE Init_Orchestrator SHALL record timestamps for the start and end of each Startup_Phase for each Language_Engine.
2. THE Init_Orchestrator SHALL log a structured startup report at the end of initialization including: total elapsed time, per-engine connection time, per-engine initialization time, number of user files loaded, number of functions registered, and any failures.
3. WHEN a startup takes longer than 10 seconds total, THE Init_Orchestrator SHALL log the report at WARNING level.
4. THE Init_Orchestrator SHALL expose startup timing data through the `NEVEN.STATUS()` function for user-facing diagnostics.
5. THE Init_Orchestrator SHALL record the number of pipe connection retries per Language_Engine for trend analysis.

### Requirement 11: Watchdog and Timeout Protection

**User Story:** As an Excel user, I want stuck initialization tasks to be automatically terminated, so that a hung language engine does not leave NEVEN in a partially initialized state indefinitely.

#### Acceptance Criteria

1. THE Init_Orchestrator SHALL enforce a maximum total initialization timeout of 60 seconds for all background tasks combined.
2. IF a background initialization task exceeds its individual timeout (15 seconds for connection, 30 seconds for startup scripts, 30 seconds per user file), THEN THE Watchdog_Timer SHALL terminate that task and mark the associated Language_Engine as Unavailable.
3. WHEN the Watchdog_Timer terminates a task, THE Init_Orchestrator SHALL log the termination reason and the task that was terminated.
4. IF the total initialization timeout is reached, THEN THE Init_Orchestrator SHALL terminate all remaining background tasks and finalize with whatever engines are available.
5. THE Watchdog_Timer SHALL not terminate tasks that are making measurable progress (receiving pipe data).

### Requirement 12: Configuration-Driven Startup Behavior

**User Story:** As a power user or administrator, I want to configure startup behavior (timeouts, parallelism, disabled engines), so that I can tune NEVEN for my specific environment.

#### Acceptance Criteria

1. THE Init_Orchestrator SHALL read startup configuration from `neven-config.json` including: per-engine connection timeout, startup script timeout, user file timeout, and maximum parallel connections.
2. WHERE a `startupPriority` field is configured for a Language_Engine, THE Init_Orchestrator SHALL use that priority to order connection attempts.
3. WHERE a `lazyConnect` field is set to true for a Language_Engine, THE Init_Orchestrator SHALL defer that engine's connection until the first function call that requires it.
4. THE Init_Orchestrator SHALL use sensible defaults when configuration values are missing: 15 seconds connection timeout, 30 seconds script timeout, 3 parallel connections.
5. WHEN configuration values are invalid (negative timeouts, zero retries), THE Init_Orchestrator SHALL log a warning and use default values.

### Requirement 13: Cancellation and Early Termination

**User Story:** As an Excel user, I want to be able to close Excel during startup without waiting for all engines to finish connecting, so that I am never trapped by a slow initialization.

#### Acceptance Criteria

1. WHEN `xlAutoClose` is called during background initialization, THE Init_Orchestrator SHALL signal all background threads to stop via a cancellation token.
2. THE Background_Connector SHALL check the cancellation token between each retry iteration of the Pipe_Connection_Loop.
3. WHEN cancellation is signaled, THE Background_Connector SHALL terminate child processes that have not yet connected and release all resources within 5 seconds.
4. THE Init_Orchestrator SHALL not block `xlAutoClose` for more than 5 seconds waiting for background threads to terminate.
5. IF background threads do not terminate within 5 seconds after cancellation, THEN THE Init_Orchestrator SHALL detach those threads and allow the process to exit (the JobObject will clean up child processes).
