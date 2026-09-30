# Implementation Plan: Reliability Improvements for RJ2XCL

## Overview

Incremental implementation of six reliability improvements across four C++ source files: `language_service.h`, `language_service.cc`, `LanguageManager.cc`, and `ConfigService.h`. Each task is ordered so that earlier changes compile and pass the existing 165 tests before later tasks build on them. New test files (`reliability_tests.cc`, `reliability_pbt.cc`) are registered in `tests/CMakeLists.txt`.

## Tasks

- [x] 1. Add HealthStatus enum and new members to `language_service.h`
  - [x] 1.1 Define the `HealthStatus` enum and add new private/public members
    - Add `enum class HealthStatus { Healthy, Unavailable, Unknown };` above the `LanguageService` class
    - Add private member `HealthStatus health_status_ = HealthStatus::Unknown;`
    - Add private member `DWORD per_language_timeout_ms_ = 0;`
    - Add public accessor `HealthStatus GetHealthStatus() const { return health_status_; }`
    - Verify the header compiles with no errors and all 165 existing tests still pass
    - _Requirements: 6.3, 6.4_

- [x] 2. Add per-language timeout getter to `ConfigService.h`
  - [x] 2.1 Implement `GetLanguageCallTimeoutMs()` in `ConfigService.h`
    - Add the `GetLanguageCallTimeoutMs(const std::string& language_name)` method that reads `config_["RJ2XCL"][language_name]["callTimeoutMs"]`
    - Return the per-language value if in range [1000, 1800000]; clamp out-of-range positive values to nearest bound; fall back to `GetCallTimeoutMs()` if absent
    - Verify all 165 existing tests still pass
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 3. Checkpoint — Verify header changes are safe
  - Ensure all 165 existing tests pass after the header-only changes in tasks 1 and 2. Ask the user if questions arise.

- [x] 4. Implement pipe validation and health check in `language_service.cc`
  - [x] 4.1 Add pre-write pipe validation at the top of `Call()`
    - Before the `retry:` label, check `connected_ && !pipe_handle_.is_valid()`
    - If true: set `connected_ = false`, set `health_status_ = HealthStatus::Unavailable`, log at WARN level with language name
    - _Requirements: 3.1, 3.2, 3.3_
  - [x] 4.2 Add process health check before `WriteFile` in `Call()`
    - After pipe validation, call `GetExitCodeProcess(process_info_.hProcess, &exit_code)`
    - If exit code is not `STILL_ACTIVE`: set `connected_ = false`, set `health_status_ = Unavailable`, log at ERROR level, set `response.set_err()` with language name and exit code, return early
    - _Requirements: 6.1, 6.2, 6.3_
  - [x] 4.3 Add pre-read pipe validation inside the read loop
    - Before each `ReadFile` call in the response-reading loop, check `!pipe_handle_.is_valid()`
    - If invalid: set error message `"[Lang] service unavailable — restart Excel to reconnect."` and break out of the loop
    - _Requirements: 3.4, 3.5_

- [x] 5. Implement user-friendly error messages in `language_service.cc`
  - [x] 5.1 Update all error messages in `Call()` to include language name and actionable guidance
    - Broken pipe on write: `"[Lang] service unavailable — restart Excel to reconnect."`
    - Read timeout: `"[Lang] did not respond within [N] seconds. Check the log file for details."`
    - Max retries exceeded: `"[Lang] reconnection failed after [N] attempts — restart Excel."`
    - Process exited during connect: `"[Lang] process exited unexpectedly (code [X]). Check the log file."`
    - Not connected: `"[Lang] is not connected — restart Excel to reconnect."`
    - Parse error: `"[Lang] returned an invalid response. Check the log file for details."`
    - Use `language_descriptor_.name_` for the language display name in every message
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 6. Implement per-language timeout usage in `language_service.cc`
  - [x] 6.1 Cache per-language timeout in the `LanguageService` constructor
    - Read `per_language_timeout_ms_` from `ConfigService::Instance().GetLanguageCallTimeoutMs(language_descriptor_.name_)`
    - _Requirements: 4.1, 4.2_
  - [x] 6.2 Use per-language timeout in `Call()` timeout selection
    - Replace the timeout selection logic: use `loading_timeout_ms_` if > 0, otherwise use `per_language_timeout_ms_`
    - _Requirements: 4.2, 4.3_

- [x] 7. Implement reconnection diagnostics logging in `language_service.cc`
  - [x] 7.1 Add structured logging at each reconnection decision point in `Call()`
    - On reconnection initiation: log at INFO level with language name, pipe name, retry attempt number, and error reason
    - On reconnection success: log at INFO level with language name, pipe name, and elapsed time (use `GetTickCount64()`)
    - On reconnection failure: log at ERROR level with language name, pipe name, Windows error code, and retry attempt number
    - On max retries exceeded: log at ERROR level with language name, total attempts, and original error
    - On process exit code during reconnection: log at WARNING level with language name and exit code
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 8. Update `Connect()` to set `health_status_` in `language_service.cc`
  - [x] 8.1 Set `health_status_` on connection success and failure in `Connect()`
    - On successful pipe connection: set `health_status_ = HealthStatus::Healthy`
    - On premature process exit: set `health_status_ = HealthStatus::Unavailable`
    - On max retries exceeded in connect: set `health_status_ = HealthStatus::Unavailable`
    - _Requirements: 1.4, 6.3_

- [x] 9. Checkpoint — Verify `language_service.cc` changes
  - Ensure all 165 existing tests pass after the `language_service.cc` changes in tasks 4–8. Ask the user if questions arise.

- [x] 10. Implement health-aware dispatch in `LanguageManager.cc`
  - [x] 10.1 Add health status check to `CallLanguage()`
    - After retrieving the service via `GetLanguageService(language_key)`, check `service->GetHealthStatus() == HealthStatus::Unavailable`
    - If unavailable: set `response.set_err(service->name() + " is currently unavailable.")` and return without calling `service->Call()`
    - _Requirements: 1.1, 1.5, 6.5_

- [x] 11. Checkpoint — Verify all production code changes
  - Ensure all 165 existing tests pass after the `LanguageManager.cc` change. All production code changes are now complete. Ask the user if questions arise.

- [x] 12. Register new test files in the build system
  - [x] 12.1 Add `reliability_tests.cc` and `reliability_pbt.cc` to `tests/CMakeLists.txt`
    - Add both filenames to the `add_executable(rj2xcl_tests ...)` source list
    - Verify the build system accepts the new entries (files will be created in subsequent tasks)
    - _Requirements: all_

- [x] 13. Write unit tests for reliability improvements
  - [x] 13.1 Create `tests/reliability_tests.cc` with unit tests for all six requirement areas
    - Include GTest/GMock headers, `language_service.h`, `ConfigService.h`, `LanguageManager.h`, and mock headers
    - **Pipe validation tests:** invalid handle with `connected_=true` → verify `connected_` set to false and error returned; invalid handle with `connected_=false` → error without crash; valid handle → no premature error
    - **Health status tests:** initial status is `Unknown`; after connect success → `Healthy`; after dead process detected → `Unavailable`; `GetHealthStatus()` returns correct value
    - **Error message tests:** broken pipe error contains language name and "restart Excel"; timeout error contains language name and seconds; max retries error contains language name and count; dead process error contains language name and exit code
    - **LanguageManager dispatch tests:** call to healthy service succeeds (mock `Call` invoked); call to unavailable service returns error without invoking `Call`; invalid key returns "invalid language key"; one unavailable service does not affect others
    - **ConfigService per-language timeout tests:** per-language present → returns per-language value; absent → returns global; both absent → returns 600000; out-of-range low (500) → clamped to 1000; out-of-range high (2000000) → clamped to 1800000; boundary values 1000 and 1800000 → returned as-is
    - _Requirements: 1.1, 1.2, 1.5, 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 4.1, 4.2, 4.3, 4.4, 4.5, 6.2, 6.3, 6.4, 6.5_

- [x] 14. Write property-based tests for correctness properties
  - [x] 14.1 Create `tests/reliability_pbt.cc` with the test fixture and random generators
    - Set up `ReliabilityPBT` test fixture with `std::mt19937` seeded at 42
    - Create generators for: random language names (1–50 chars, alphanumeric), random exit codes (0–255 excluding 259), random timeout values (INT_MIN to INT_MAX), random valid timeouts (1000–1800000)
    - Follow the existing `python_sandbox_pbt.cc` pattern (custom generators within GTest, minimum 100 iterations)
    - _Requirements: all_
  - [ ]* 14.2 Write property test for failure isolation (Property 1)
    - **Property 1: Failure Isolation**
    - Generate random sets of 1–5 mock services with random health statuses; mark one as Unavailable; verify all others retain their original status
    - **Validates: Requirements 1.1, 1.5**
  - [ ]* 14.3 Write property test for error messages containing language name (Property 2)
    - **Property 2: Error Messages Always Contain Language Name**
    - Generate random language names (1–50 chars, alphanumeric); trigger each error path; verify language name appears as substring in the error string
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**
  - [ ]* 14.4 Write property test for error message formatting with context values (Property 3)
    - **Property 3: Error Message Formatting Includes Context Values**
    - Generate random language names and random numeric context values (0–2^31); verify each error template contains both the language name and the string representation of the numeric value
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4**
  - [ ]* 14.5 Write property test for per-language timeout override (Property 4)
    - **Property 4: Per-Language Timeout Override**
    - Generate random language names and random valid timeouts (1000–1800000); build config JSON with per-language value; verify `GetLanguageCallTimeoutMs()` returns the per-language value
    - **Validates: Requirements 4.1, 4.2**
  - [ ]* 14.6 Write property test for timeout value clamping (Property 5)
    - **Property 5: Timeout Value Clamping**
    - Generate random integers (INT_MIN to INT_MAX); verify `GetLanguageCallTimeoutMs()` always returns a value in [1000, 1800000] for positive inputs, and falls back to global for non-positive inputs
    - **Validates: Requirements 4.4, 4.5**
  - [ ]* 14.7 Write property test for health-aware dispatch (Property 6)
    - **Property 6: Health-Aware Dispatch Skips Unavailable Services**
    - Generate random language names; set health to Unavailable; call `CallLanguage()`; verify error contains language name and `Call()` was not invoked on the mock
    - **Validates: Requirements 6.5**
  - [ ]* 14.8 Write property test for dead process detection (Property 7)
    - **Property 7: Dead Process Detection Sets Correct State and Error**
    - Generate random language names and random exit codes (0–255, excluding 259); verify `health_status_` is set to `Unavailable`, `connected_` is `false`, and error string contains both language name and exit code
    - **Validates: Requirements 1.2, 6.2, 6.3**

- [x] 15. Final checkpoint — Verify all tests pass
  - Ensure all 165 existing tests plus the new reliability tests pass. Ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints at tasks 3, 9, 11, and 15 ensure incremental validation against the 165 existing tests
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- All changes are confined to four production files (`language_service.h`, `language_service.cc`, `LanguageManager.cc`, `ConfigService.h`) plus two new test files
