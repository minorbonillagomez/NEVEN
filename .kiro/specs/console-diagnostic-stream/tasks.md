# Implementation Plan: Console Diagnostic Stream

## Overview

This plan implements a diagnostic message stream that routes stdout/stderr output from R, Julia, and Python cell executions to the WebView2 REPL console. The implementation proceeds bottom-up: protobuf schema changes first, then the C++ routing infrastructure, then the JavaScript UI, and finally integration wiring.

## Tasks

- [x] 1. Extend protobuf schema and regenerate
  - [x] 1.1 Add `console_output` and `console_error_output` fields to `CallResponse` in `PB/variable.proto`
    - Add `string console_output = 11;` outside the `oneof operation` block for Python stdout
    - Add `string console_error_output = 12;` outside the `oneof operation` block for Python stderr
    - Add comments explaining these are for Python diagnostic piggybacking
    - Regenerate protobuf C++ and JS files via the existing build process
    - _Requirements: 3.3, 3.4_

- [x] 2. Implement DiagnosticRouter core component
  - [x] 2.1 Create `Common/DiagnosticRouter.h` with the DiagnosticMessage struct and DiagnosticRouter class
    - Define `DiagnosticMessage` struct with `language`, `type`, `text`, `timestamp` fields
    - Define `DiagnosticRouter` singleton class with `Route()`, `RoutePythonDiagnostics()`, `DeliverPending()`, `FlushBufferToConsole()`, `SetEnabled()`, `Shutdown()` methods
    - Define internal `LanguageBuffer` struct with 200-message circular buffer and FIFO eviction
    - Include thread-safe queue (`std::mutex` + `std::deque<DiagnosticMessage>`) for pending messages
    - Include per-language `OutputBuffer` map protected by `buffer_mutex_`
    - _Requirements: 1.1, 1.2, 1.3, 5.3, 7.1, 7.2, 9.1, 9.3_

  - [x] 2.2 Implement `Common/DiagnosticRouter.cc`
    - Implement `Route()`: extract text/err from `Console` protobuf, map to "output"/"warning" type, timestamp via `std::chrono`, enqueue to `pending_queue_`
    - Implement `RoutePythonDiagnostics()`: split `console_output`/`console_error_output` strings into lines, create DiagnosticMessages with language "Python"
    - Implement `DeliverPending()`: swap deque under lock, iterate messages, call `REPLBridge::SendDiagnostic()` if console open, else push to `OutputBuffer`
    - Implement `FlushBufferToConsole()`: drain all language buffers, call `REPLBridge::SendDiagnosticBatch()`
    - Implement `SetEnabled()`/`IsEnabled()` toggle
    - Implement `Shutdown()` to clear queues and buffers
    - Discard malformed messages (empty text and empty err) with `RJ2XCL_LOG_WARN`
    - _Requirements: 1.1, 1.2, 1.3, 1.5, 3.4, 5.3, 5.4, 6.1, 6.4, 7.1, 7.2, 7.3, 9.1, 9.4_

  - [x] 2.3 Add `DiagnosticRouter.cc` to `Common/CMakeLists.txt`
    - Add the new source file to the `COMMON_SOURCES` list
    - _Requirements: N/A (build integration)_

  - [ ]* 2.4 Write property tests for DiagnosticMessage type mapping (Property 1)
    - **Property 1: Console message type mapping**
    - Generate random Console protobuf messages with text or err set
    - Verify DiagnosticRouter produces correct `type` ("output" for text, "warning" for err)
    - Verify message text is preserved exactly
    - **Validates: Requirements 1.1, 1.2, 2.1, 2.2**

  - [ ]* 2.5 Write property tests for OutputBuffer capacity and eviction (Property 4)
    - **Property 4: Buffer capacity with FIFO eviction**
    - Generate sequences of N messages (varying N from 0 to 500)
    - Verify buffer contains exactly `min(N, 200)` messages
    - Verify retained messages are the most recent ones in chronological order
    - **Validates: Requirements 5.3, 7.1, 7.2**

  - [ ]* 2.6 Write property tests for buffer flush (Property 5)
    - **Property 5: Buffer flush delivers all and clears**
    - Generate non-empty buffer states, call FlushBufferToConsole()
    - Verify all messages delivered in chronological order
    - Verify buffer is empty after flush
    - **Validates: Requirements 5.4, 7.3**

  - [ ]* 2.7 Write property tests for queue ordering (Property 3)
    - **Property 3: Queue ordering preservation**
    - Generate sequences of N messages enqueued from multiple languages
    - Drain queue and verify FIFO ordering is preserved
    - **Validates: Requirements 1.5**

  - [ ]* 2.8 Write property tests for thread-safe concurrent enqueue (Property 10)
    - **Property 10: Thread-safe concurrent enqueue**
    - Push M messages from N threads (N ≥ 2) concurrently
    - Drain queue and verify total count equals M, each message appears exactly once
    - **Validates: Requirements 9.1, 9.2, 9.3**

- [x] 3. Extend REPLBridge for diagnostic delivery
  - [x] 3.1 Add `SendDiagnostic()` and `SendDiagnosticBatch()` to `Common/REPLBridge.h`
    - Declare `static void SendDiagnostic(const std::string& viewer_id, const std::string& language, const std::string& type, const std::string& text, int64_t timestamp)`
    - Declare `static void SendDiagnosticBatch(const std::string& viewer_id, const std::vector<DiagnosticMessage>& messages)`
    - _Requirements: 5.1, 5.2_

  - [x] 3.2 Implement `SendDiagnostic()` and `SendDiagnosticBatch()` in `Common/REPLBridge.cc`
    - Build JSON with `action: "diagnostic"`, `language`, `type`, `text`, `timestamp` fields
    - Call `ViewerManager::SendToViewer()` via `PostWebMessageAsJson`
    - For batch: build JSON with `action: "diagnostic-batch"` and `messages` array
    - _Requirements: 5.1, 5.2, 5.5_

  - [ ]* 3.3 Write property test for JSON serialization round-trip (Property 9)
    - **Property 9: Diagnostic JSON serialization round-trip**
    - Generate random DiagnosticMessage structs (non-empty language, type, text, positive timestamp)
    - Serialize to JSON protocol format, parse back, verify all fields preserved
    - **Validates: Requirements 5.1**

- [x] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Intercept kConsole in RunCallbackThread
  - [x] 5.1 Modify `Core/src/language_service.cc` RunCallbackThread to intercept `kConsole` messages
    - After `Unframe(call, ...)`, check `call.operation_case() == kConsole`
    - If kConsole: call `DiagnosticRouter::Instance().Route(language_descriptor_.name_, call.console())`
    - Do NOT call `engine->HandleCallback()` for console messages
    - Do NOT write a response back on the pipe
    - Restart the read immediately (ResetEvent + ReadFile + continue)
    - Preserve existing path for kFunctionCall, kFunctionList, user_command, etc.
    - _Requirements: 1.3, 1.4, 6.1, 6.2, 6.3, 6.5_

  - [ ]* 5.2 Write property test for operation case dispatch (Property 2)
    - **Property 2: Operation case dispatch correctness**
    - Generate random CallResponse messages with various operation_case values
    - Verify kConsole routes to DiagnosticRouter and NOT to HandleCallback
    - Verify kFunctionCall routes to HandleCallback and NOT to DiagnosticRouter
    - **Validates: Requirements 1.3, 6.1, 6.2**

- [x] 6. Implement Python diagnostic capture
  - [x] 6.1 Add `_DiagnosticCapture` class to `startup/startup.py`
    - Implement `_DiagnosticCapture` with `write()`, `flush()`, `get_and_clear()` methods
    - Enforce 64 KB hard limit with `[...truncated...]` marker on overflow
    - Create `_diag_stdout` and `_diag_stderr` instances
    - Redirect `sys.stdout` and `sys.stderr` to the capture instances during cell execution
    - Restore original stdout/stderr after execution completes
    - _Requirements: 3.1, 3.2, 3.5_

  - [x] 6.2 Modify `ControlPython/src/python_interface.cc` to populate `console_output` fields
    - After Python function execution completes, call `get_and_clear()` on both capture buffers
    - Set `response.set_console_output(stdout_text)` and `response.set_console_error_output(stderr_text)`
    - Only populate fields if non-empty
    - _Requirements: 3.3, 3.4_

  - [x] 6.3 Modify XLL response handler to route Python diagnostics
    - When receiving a Python function response, check if `console_output` or `console_error_output` is non-empty
    - Call `DiagnosticRouter::Instance().RoutePythonDiagnostics()` with the captured text
    - _Requirements: 3.4_

  - [ ]* 6.4 Write property tests for Python capture buffer (Property 6)
    - **Property 6: Python capture buffer accumulation**
    - Generate random string sequences, write to DiagnosticCapture
    - Verify `get_and_clear()` returns concatenation in order
    - Verify buffer is empty after `get_and_clear()`
    - **Validates: Requirements 3.1, 3.2**

  - [ ]* 6.5 Write property tests for Python buffer truncation (Property 7)
    - **Property 7: Python buffer truncation at 64KB**
    - Generate strings whose total exceeds 64 KB
    - Verify buffer does not exceed 64 KB + truncation indicator length
    - Verify buffer ends with `[...truncated...]`
    - **Validates: Requirements 3.5**

  - [ ]* 6.6 Write property test for Python response routing (Property 8)
    - **Property 8: Python response diagnostic routing**
    - Generate non-empty `console_output` strings
    - Verify `RoutePythonDiagnostics()` produces DiagnosticMessages with language "Python"
    - Verify stdout maps to type "output" and stderr maps to type "warning"
    - **Validates: Requirements 3.4**

- [x] 7. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Implement STA timer for queue draining
  - [x] 8.1 Add a 50ms Windows timer in ViewerManager's STA thread for diagnostic delivery
    - Use `SetTimer()` with a callback that calls `DiagnosticRouter::Instance().DeliverPending()`
    - Ensure timer is created on the STA thread
    - Kill timer on shutdown (`KillTimer`)
    - _Requirements: 1.4, 9.4_

  - [x] 8.2 Implement console-open detection in `DeliverPending()`
    - Check if REPL viewer is active before calling `SendDiagnostic()`
    - If viewer not available, push messages to OutputBuffer instead
    - If `SendToViewer()` fails (viewer closed mid-delivery), re-buffer the message
    - _Requirements: 5.3, 7.1_

- [x] 9. Implement JavaScript diagnostic handler in repl.html
  - [x] 9.1 Add diagnostic state to the JavaScript state object
    - Add `state.diagnosticsEnabled = true` (global toggle, default enabled)
    - Add `state.filters = { output: true, warning: true }` (per-type filters)
    - Add `state.tabs[lang].bufferedDiagnostics = []` for each language
    - Add `state.tabs[lang].unreadCount = 0` for badge counter
    - _Requirements: 8.4, 10.4_

  - [x] 9.2 Implement `handleDiagnostic(msg)` function
    - Route message to correct language tab based on `msg.language`
    - Check `state.diagnosticsEnabled` — if disabled, buffer in `bufferedDiagnostics`
    - Check `state.filters[msg.type]` — if filtered out, skip display
    - Format with `[Language]` prefix
    - Apply CSS class: `diagnostic warning` (amber) for warnings, `diagnostic output` (muted) for output
    - Add left border styling to distinguish from interactive REPL output
    - Increment `unreadCount` and update tab badge if message arrives on non-active tab
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7_

  - [x] 9.3 Add `"diagnostic"` and `"diagnostic-batch"` cases to the message event listener
    - Handle `"diagnostic"` action by calling `handleDiagnostic(msg)`
    - Handle `"diagnostic-batch"` action by iterating `msg.messages` and calling `handleDiagnostic()` for each
    - _Requirements: 5.1, 5.4_

  - [x] 9.4 Implement diagnostics toggle button in the tab bar
    - Add a toggle button/checkbox labeled "Diagnostics" in the tab bar area
    - When toggled off: hide diagnostic messages, continue buffering
    - When toggled on: flush `bufferedDiagnostics` to display in order, clear buffer
    - Persist toggle state in session (JavaScript variable, not localStorage)
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

  - [x] 9.5 Implement severity filter controls
    - Add filter toggles for "output" and "warning" types
    - When a filter is toggled, immediately update visible messages (show/hide matching entries)
    - Default both filters to enabled
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

  - [x] 9.6 Add CSS styles for diagnostic messages
    - `.diagnostic` base class: left border, slightly different background tint
    - `.diagnostic.warning`: amber/yellow text color (use existing `--text-warning`)
    - `.diagnostic.output`: muted/secondary text color (use existing `--text-secondary`)
    - Tab badge styling for unread count
    - _Requirements: 4.2, 4.3, 4.4_

  - [ ]* 9.7 Write property tests for tab routing (Property 11)
    - **Property 11: Tab routing correctness**
    - Generate diagnostic messages with random language values from {"R", "Julia", "Python"}
    - Verify each message is appended to the correct language panel only
    - **Validates: Requirements 4.5**

  - [ ]* 9.8 Write property tests for badge increment (Property 12)
    - **Property 12: Badge increment on cross-tab message**
    - Generate messages where language ≠ activeTab
    - Verify unreadCount increments by 1 for each cross-tab message
    - Verify no increment when language == activeTab
    - **Validates: Requirements 4.6**

  - [ ]* 9.9 Write property tests for toggle buffer/flush (Properties 13, 14)
    - **Property 13: Toggle disable buffers without display**
    - **Property 14: Toggle re-enable flushes buffered**
    - Generate messages while disabled, verify buffered not displayed
    - Transition to enabled, verify all buffered messages flushed in order
    - **Validates: Requirements 8.2, 8.3**

  - [ ]* 9.10 Write property tests for filter visibility (Property 15)
    - **Property 15: Filter visibility**
    - Generate messages with random types and random filter states
    - Verify visible messages match exactly those whose type has an enabled filter
    - **Validates: Requirements 10.2, 10.3, 10.5**

  - [ ]* 9.11 Write property test for display prefix formatting (Property 16)
    - **Property 16: Display prefix formatting**
    - Generate messages with random language and text
    - Verify rendered output contains `[Language]` prefix followed by text
    - **Validates: Requirements 4.1**

- [x] 10. Wire FlushBufferToConsole on console open
  - [x] 10.1 Call `DiagnosticRouter::Instance().FlushBufferToConsole()` when REPL console opens
    - Hook into `REPLManager::ShowConsole()` or the viewer-ready callback
    - Deliver buffered messages within 500ms of console becoming ready
    - _Requirements: 5.4, 7.3_

- [x] 11. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- The project uses GTest v1.14.0 with custom random generators for property-based tests (see `webview2_pbt.cc` pattern)
- JavaScript property tests use fast-check + Jest/Vitest
- C++ code follows project conventions: `snake_case` functions, `PascalCase` classes, `.cc/.h` files
