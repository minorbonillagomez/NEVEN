# Implementation Plan: Startup Optimization

## Overview

Transform NEVEN's monolithic `Init()` method into a two-phase architecture: a fast synchronous phase (≤3s on UI thread) followed by parallel asynchronous background initialization. Implementation proceeds bottom-up: core data types and utilities first, then individual components, then integration and wiring into the existing `rj2xcl.cc` entry point.

All new code lives in `Common/` under the `neven::` namespace with `Neven` file prefix. Tests use GTest v1.14.0 with RapidCheck for property-based testing.

## Tasks

- [x] 1. Set up project structure, enums, and shared data types
  - [x] 1.1 Create `Common/NevenStartupTypes.h` with all shared enums and structs
    - Define `neven::StartupPhase` enum (Configure, Connect, Initialize, LoadFiles, Register, Complete)
    - Define `neven::InitState` enum (NotStarted, Connecting, Ready, Failed)
    - Define `neven::HealthStatus` enum (Pending, Connecting, Healthy, LoadingFiles, Ready, Degraded, Unavailable)
    - Define `neven::EngineTimingData` struct with all timing fields
    - Define `neven::StartupReport` struct
    - Define `neven::StartupConfig` struct (parsed from neven-config.json)
    - _Requirements: 1.5, 1.6, 2.2, 2.3, 10.1_

  - [x] 1.2 Create `Common/NevenStartupConfig.h/.cc` — configuration parser
    - Implement `parse_startup_config()` that reads the `"startup"` section from neven-config.json via existing `ConfigService`
    - Implement per-engine priority and `lazyConnect` parsing
    - Validate values: negative/zero/out-of-range → log warning, use defaults (15000ms connection, 30000ms script, 30000ms file, 60000ms total, 3 parallel)
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_

  - [ ]* 1.3 Write property test for configuration validation (Property 14)
    - **Property 14: Configuration validation with sensible defaults**
    - Generate arbitrary invalid config values (negative, zero, extremely large, missing fields)
    - Verify defaults are always applied for invalid/missing values
    - **Validates: Requirements 12.4, 12.5**

  - [ ]* 1.4 Write unit tests for `NevenStartupConfig`
    - Test valid config parsing
    - Test missing fields → defaults
    - Test invalid values → warning logged + defaults
    - Test per-engine priority ordering
    - _Requirements: 12.1, 12.2, 12.4, 12.5_

  - [x] 1.5 Update `Common/CMakeLists.txt` to include new source files
    - Add `NevenStartupTypes.h`, `NevenStartupConfig.h`, `NevenStartupConfig.cc`
    - _Requirements: N/A (build infrastructure)_

- [x] 2. Implement StatusBarReporter
  - [x] 2.1 Create `Common/NevenStatusBarReporter.h/.cc`
    - Implement `neven::StatusBarReporter` singleton with `ReportProgress()`, `ReportEngineReady()`, `ReportComplete()`, `Clear()`
    - Implement 1-second throttling using `GetTickCount()` comparison
    - Use `xlcMessage` via existing Excel bridge for status bar updates
    - Schedule clear after 5 seconds on completion using `SetTimer`
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

  - [ ]* 2.2 Write property test for status bar rate limiting (Property 18)
    - **Property 18: Status bar update rate limiting**
    - Generate arbitrary sequences of `ReportProgress()` calls with random timestamps
    - Verify at most 1 actual update per 1-second window
    - **Validates: Requirements 9.4**

  - [ ]* 2.3 Write unit tests for StatusBarReporter
    - Test throttling behavior (multiple calls within 1s → only first updates)
    - Test `ReportEngineReady` message format
    - Test `ReportComplete` summary format
    - Test elapsed time inclusion after 10 seconds
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [x] 3. Implement WatchdogTimer
  - [x] 3.1 Create `Common/NevenWatchdogTimer.h/.cc`
    - Implement `neven::WatchdogTimer` with `Start()`, `Stop()`, `RegisterTask()`, `ReportProgress()`
    - Watchdog runs on dedicated thread via `_beginthreadex`
    - Uses `WaitForSingleObject` on stop event with periodic wake-up (1s interval)
    - Checks per-task timeouts and total timeout
    - On timeout: sets cancellation token, logs termination reason
    - Progress reports reset individual task timer
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

  - [ ]* 3.2 Write property test for watchdog progress respect (Property 19)
    - **Property 19: Watchdog respects progress reports**
    - Generate arbitrary task sequences with progress reports before timeout
    - Verify watchdog does NOT terminate tasks that report progress in time
    - **Validates: Requirements 11.5**

  - [ ]* 3.3 Write property test for watchdog stuck task termination (Property 20)
    - **Property 20: Watchdog terminates stuck tasks**
    - Generate arbitrary tasks that do NOT report progress within timeout
    - Verify watchdog terminates them and sets HealthStatus to Unavailable
    - **Validates: Requirements 11.2**

  - [ ]* 3.4 Write unit tests for WatchdogTimer
    - Test total timeout triggers cancellation
    - Test individual task timeout detection
    - Test `Stop()` cleanly terminates watchdog thread
    - Test progress report resets timer
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

- [x] 4. Checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Implement ProgressiveRegistrar
  - [x] 5.1 Create `Common/NevenProgressiveRegistrar.h/.cc`
    - Implement `neven::ProgressiveRegistrar` singleton with `EnqueueRegistration()`, `ProcessPendingRegistrations()`, `IsRegistered()`, `HasPending()`, `AllComplete()`
    - Thread-safe queue (`std::queue<uint32_t>` protected by `queue_mutex_`)
    - `ProcessPendingRegistrations()` calls `xlfRegister` via existing `register_functions()` path for each pending engine
    - Track registered engines in `std::set<uint32_t>` to prevent duplicates
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

  - [x] 5.2 Create the `NEVEN_ProgressiveRegister` exported function and timer callback
    - Implement `RegistrationTimerProc` — `SetTimer` callback that checks pending queue and calls `ProcessPendingRegistrations()`
    - Implement exported `NEVEN_ProgressiveRegister()` XLL function
    - Add `NEVEN_ProgressiveRegister` to the `.def` file for export
    - _Requirements: 5.2, 7.3_

  - [ ]* 5.3 Write property test for no duplicate registrations (Property 7)
    - **Property 7: No duplicate function registrations**
    - Generate arbitrary sequences of `EnqueueRegistration()` calls (including duplicates)
    - Verify each engine is registered at most once
    - **Validates: Requirements 5.3**

  - [ ]* 5.4 Write property test for completion triggers registration (Property 6)
    - **Property 6: Completion triggers progressive registration**
    - Generate arbitrary engine completion sequences
    - Verify registration enqueued exactly once per completed engine, never for incomplete engines
    - **Validates: Requirements 3.3, 4.2, 5.1**

  - [ ]* 5.5 Write unit tests for ProgressiveRegistrar
    - Test enqueue from multiple threads simultaneously
    - Test `ProcessPendingRegistrations` calls xlfRegister for each pending engine
    - Test `AllComplete()` returns true only when all expected engines registered
    - Test timer callback kills timer when all complete
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 6. Implement BackgroundConnector
  - [x] 6.1 Create `Common/NevenBackgroundConnector.h/.cc`
    - Implement `neven::BackgroundConnector` with `ConnectEngine()`, `WaitAll()`, `GetThreadHandle()`
    - `ConnectEngine()` launches a worker thread via `_beginthreadex`
    - Worker thread function `EngineWorker()` performs: pipe connection retry loop → startup script → file loading → enqueue registration
    - Exponential backoff: 50ms initial, doubling up to 800ms cap, total bounded by connection timeout
    - Check cancellation token between each retry iteration
    - Detect child process exit via `GetExitCodeProcess` — abort immediately if process dead
    - On success: update `HealthStatus` to `Healthy`, record timing
    - On failure: update `HealthStatus` to `Unavailable`, log warning with elapsed time
    - No locks held during blocking I/O (pipe ops, Sleep)
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 3.1, 3.2, 3.4, 3.5, 4.1, 4.3, 4.4, 4.5, 4.6, 4.7, 7.1, 7.5, 7.6_

  - [x] 6.2 Implement startup script execution in the worker thread
    - After pipe connection succeeds, send startup script via existing `LanguageService::Initialize()`
    - Timeout after `scriptTimeoutMs` — set `Degraded` on timeout/failure
    - Record execution time in `EngineTimingData`
    - Report progress to watchdog during script execution
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

  - [x] 6.3 Implement user function file loading in the worker thread
    - After startup script completes, load user files via existing `ReadSourceFile()` path
    - Per-file timeout of `fileTimeoutMs` — skip file on timeout, log warning, continue
    - Detect engine crash during file loading → mark Unavailable, skip remaining files
    - Load files in parallel across different engines (each engine's worker handles its own files)
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7_

  - [ ]* 6.4 Write property test for exponential backoff (Property 4)
    - **Property 4: Exponential backoff retry delays**
    - Generate arbitrary retry counts (1–20)
    - Verify delay_i = min(50 * 2^i, 800) for each retry
    - Verify total elapsed does not exceed connection timeout
    - **Validates: Requirements 2.6**

  - [ ]* 6.5 Write property test for priority-based connection ordering (Property 5)
    - **Property 5: Priority-based connection ordering**
    - Generate arbitrary engine configs with random priority values
    - Verify thread launch order matches ascending priority
    - **Validates: Requirements 2.7, 12.2**

  - [ ]* 6.6 Write property test for health status correctness (Property 3)
    - **Property 3: Health status correctly reflects connection outcome**
    - Generate arbitrary connection outcomes (success, timeout, crash)
    - Verify final status is Healthy iff pipe succeeded, Unavailable otherwise
    - Verify no engine remains in Connecting state after completion
    - **Validates: Requirements 2.2, 2.3, 2.4**

  - [ ]* 6.7 Write property test for cooperative cancellation (Property 16)
    - **Property 16: Cooperative cancellation at retry boundaries**
    - Generate arbitrary retry sequences, set cancellation at random points
    - Verify loop exits within one additional retry iteration
    - **Validates: Requirements 13.1, 13.2**

  - [ ]* 6.8 Write property test for file loading ordering (Property 11)
    - **Property 11: File loading respects startup script ordering**
    - Generate arbitrary engine states (script success/failure)
    - Verify files never load before startup script completes
    - Verify no files load if startup script fails
    - **Validates: Requirements 4.4**

  - [ ]* 6.9 Write property test for file timeout skip-and-continue (Property 12)
    - **Property 12: File timeout results in skip-and-continue**
    - Generate arbitrary file lists with random timeout positions
    - Verify all subsequent files are still attempted after a timeout
    - **Validates: Requirements 4.3**

  - [ ]* 6.10 Write property test for engine crash during file loading (Property 13)
    - **Property 13: Engine crash during file loading skips remaining files**
    - Generate arbitrary file lists with crash at random position
    - Verify remaining files are NOT attempted, status → Unavailable
    - **Validates: Requirements 4.7**

  - [ ]* 6.11 Write property test for failure isolation (Property 8)
    - **Property 8: Failure isolation — failed engines do not block others**
    - Generate arbitrary subsets of failing engines (K out of N)
    - Verify remaining N-K engines complete full initialization independently
    - **Validates: Requirements 8.1**

  - [ ]* 6.12 Write property test for telemetry timing invariants (Property 17)
    - **Property 17: Telemetry completeness and timing invariants**
    - Generate arbitrary engine completion sequences
    - Verify connect_end >= connect_start, init_end >= init_start, files_end >= files_start
    - Verify retry_count matches actual retries performed
    - **Validates: Requirements 3.5, 10.1, 10.5**

  - [ ]* 6.13 Write unit tests for BackgroundConnector
    - Test successful connection with mock pipe
    - Test retry exhaustion → Unavailable
    - Test child process exit detection → immediate abort
    - Test cancellation token stops retry loop
    - Test WaitAll with timeout
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 13.2_

- [x] 7. Checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Implement InitOrchestrator
  - [x] 8.1 Create `Common/NevenInitOrchestrator.h/.cc`
    - Implement `neven::InitOrchestrator` singleton with `FastInit()`, `GetInitState()`, `GetEngineHealth()`, `GetStartupReport()`, `CancelAndWait()`, `IsEngineReady()`, `GetEngineStatusMessage()`
    - `FastInit()` performs UI-thread work: read config, configure languages, create JobObject, register placeholders, set `InitState::Connecting`, launch BackgroundConnector threads, start WatchdogTimer, start registration timer
    - `BackgroundInitSequence()` coordinates the background phase (launched as coordinator thread)
    - `OnEngineReady()` called by workers — enqueues registration, updates StatusBarReporter
    - `CancelAndWait()` sets cancellation token, waits up to 5s for threads, then detaches
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 7.1, 7.2, 7.3, 7.4, 7.5, 8.1, 8.3, 8.4, 13.1, 13.3, 13.4, 13.5_

  - [x] 8.2 Implement placeholder/stub function registration in `FastInit()`
    - Register placeholder functions for all configured engines before returning
    - Stubs return "Engine connecting..." or "Engine unavailable" messages depending on state
    - Use existing `xlfRegister` path with placeholder type signatures
    - _Requirements: 1.4, 6.2, 6.3, 8.2, 8.5_

  - [x] 8.3 Implement graceful degradation and stub functions
    - When engine is Unavailable: register stubs that return error message with engine name + troubleshooting hint
    - When engine is Connecting: return message indicating still starting with estimated time if available
    - If all engines fail: ensure basic XLL functions (help, version, status) remain available
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 6.2, 6.3_

  - [x] 8.4 Implement startup telemetry and `NEVEN.STATUS()` data provider
    - Record timestamps for start/end of each phase per engine
    - Log structured startup report at end of initialization
    - Log at WARNING level if total startup > 10 seconds
    - Expose timing data for `NEVEN.STATUS()` function
    - Record retry counts per engine
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

  - [ ]* 8.5 Write property test for all engines dispatched (Property 1)
    - **Property 1: All configured engines are dispatched to background threads**
    - Generate arbitrary engine configs (1–5 engines, some lazy)
    - Verify non-lazy engines all have worker threads launched after FastInit
    - **Validates: Requirements 1.3, 2.1**

  - [ ]* 8.6 Write property test for placeholder registration coverage (Property 2)
    - **Property 2: Placeholder registration covers all configured engines**
    - Generate arbitrary engine configs
    - Verify placeholders registered for ALL engines (including lazy ones)
    - **Validates: Requirements 1.4**

  - [ ]* 8.7 Write property test for lazy connect deferral (Property 15)
    - **Property 15: Lazy connect defers connection**
    - Generate configs with random lazyConnect flags
    - Verify no background thread launched for lazy engines during FastInit
    - **Validates: Requirements 12.3**

  - [ ]* 8.8 Write property test for unavailable engines produce stubs (Property 9)
    - **Property 9: Unavailable engines produce stub functions**
    - Generate arbitrary engines with Unavailable status
    - Verify all functions registered as stubs returning error with engine name
    - **Validates: Requirements 8.2, 8.5**

  - [ ]* 8.9 Write property test for status-aware function dispatch (Property 10)
    - **Property 10: Status-aware function dispatch**
    - Generate arbitrary engine states (Connecting, Unavailable)
    - Verify correct message type returned for each state, always containing engine name
    - **Validates: Requirements 6.2, 6.3**

  - [ ]* 8.10 Write unit tests for InitOrchestrator
    - Test FastInit returns within 3 seconds with mock services
    - Test CancelAndWait terminates within 5 seconds
    - Test GetStartupReport contains all engine data
    - Test GetEngineStatusMessage for each HealthStatus value
    - Test all-engines-fail scenario still provides basic functions
    - _Requirements: 1.1, 8.4, 10.2, 13.4_

- [x] 9. Checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. Wire into existing codebase
  - [x] 10.1 Modify `Core/src/rj2xcl.cc` — delegate `Init()` to `FastInit()`
    - In the existing `Init()` method (called from `xlAutoOpen`), replace the sequential initialization with a call to `neven::InitOrchestrator::Instance().FastInit()`
    - Pass existing `job_handle`, `callback_info`, and `object_map` references
    - Remove or guard the old sequential `LanguageService::Connect()` calls
    - Ensure `xlAutoOpen` returns promptly after `FastInit()`
    - _Requirements: 1.1, 1.2, 1.3_

  - [x] 10.2 Modify `Core/src/rj2xcl.cc` — update `xlAutoClose` for cancellation
    - In `xlAutoClose`, call `neven::InitOrchestrator::Instance().CancelAndWait(5000)` before existing cleanup
    - Ensure background threads are signaled and waited on before resource release
    - _Requirements: 7.4, 13.1, 13.3, 13.4, 13.5_

  - [x] 10.3 Modify `Core/src/basic_functions.cc` — implement `NEVEN.STATUS()` function
    - Implement the `NEVEN.STATUS()` Excel function that queries `InitOrchestrator::GetStartupReport()`
    - Format output as multi-line string with per-engine status, timing, and function counts
    - Register the function in the XLL function table
    - _Requirements: 6.5, 10.4_

  - [x] 10.4 Update `.def` file with new export
    - Add `NEVEN_ProgressiveRegister` to the exports definition file
    - _Requirements: 5.2_

  - [x] 10.5 Update `Common/CMakeLists.txt` with all new source files
    - Add all `Neven*.h` and `Neven*.cc` files to the Common library sources
    - Ensure proper include paths for new headers
    - _Requirements: N/A (build infrastructure)_

  - [ ]* 10.6 Write integration tests for end-to-end startup
    - Test full startup sequence with MockLanguageService (configurable delays/failures)
    - Verify all functions registered after successful startup
    - Verify graceful degradation when engines fail
    - Verify xlAutoClose during init results in clean shutdown
    - _Requirements: 1.1, 2.5, 7.4, 8.1, 8.4, 13.4_

- [x] 11. Final checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document (Properties 1–20)
- Unit tests validate specific examples and edge cases
- All new code uses `neven::` namespace and `Neven` file prefix per design conventions
- Existing `rj2xcl::` code is called via bridge pattern — no ABI-breaking changes
- RapidCheck library needed for property-based tests (integrates with GTest)
- The `.def` file export and `SetTimer` callback are critical for progressive registration to work on the UI thread
