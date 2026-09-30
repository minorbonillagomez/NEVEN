# Implementation Plan: WebView2 REPL Console

## Overview

Replace the obsolete Electron-based console with a lightweight REPL console running inside the existing WebView2 viewer subsystem. Implementation proceeds bottom-up: data models and history logic first, then the bridge layer, then WindowManager integration, and finally the HTML UI — wiring everything together at the end.

## Tasks

- [x] 1. Create REPLManager singleton with command history logic
  - [x] 1.1 Create `Common/REPLManager.h` with class declaration
    - Define the `REPLManager` singleton class with `ShowConsole()`, `HideConsole()`, `Shutdown()`, `IsConsoleOpen()`, `GetConsoleViewerId()` methods
    - Define `AddToHistory()`, `GetHistory()`, `GetLastActiveLanguage()`, `SetLastActiveLanguage()` methods
    - Define the `LanguageHistory` struct with `std::deque<std::string>`, `MAX_HISTORY = 500`, and `Add()` method implementing deduplication and bounded buffer
    - Include mutex for thread safety
    - _Requirements: 1.1, 1.2, 1.4, 1.6, 4.3, 4.4, 4.6_

  - [x] 1.2 Create `Common/REPLManager.cc` with implementation
    - Implement singleton `Instance()` with static local
    - Implement `ShowConsole()`: check `ViewerManager::IsAvailable()`, return error if not; if `console_viewer_id_` is set and viewer alive, bring to front via `ViewerManager::SendToViewer()`; otherwise create viewer via `ViewerManager::CreateViewerFromFile()` using `%NEVEN_HOME%/console/repl.html`
    - Implement `HideConsole()`: close or hide the viewer window
    - Implement `Shutdown()`: close viewer, clear state
    - Implement `AddToHistory()`: skip consecutive duplicates, enforce 500-entry cap with `pop_front()`
    - Implement `GetHistory()`, `GetLastActiveLanguage()`, `SetLastActiveLanguage()`
    - _Requirements: 1.1, 1.2, 1.4, 1.6, 1.7, 2.5, 4.3, 4.4, 4.6_

  - [ ]* 1.3 Write property tests for REPLManager command history
    - **Property 10: History Bounded Buffer** — Generate N commands (N from 1..2000), verify history size ≤ 500 and contains the N most recent commands in order
    - **Validates: Requirements 4.3**

  - [ ]* 1.4 Write property tests for history deduplication and isolation
    - **Property 12: Consecutive Command Deduplication** — Generate random command, repeat K times (K from 2..10), verify only one entry at end
    - **Property 3: Command History Language Isolation** — Generate commands for two languages, verify adding to one does not modify the other
    - **Validates: Requirements 4.6, 2.6**

  - [ ]* 1.5 Write property test for singleton guarantee
    - **Property 1: Console Singleton Guarantee** — Generate random sequences of ShowConsole/Shutdown calls, verify at most 1 active viewer at any time
    - **Validates: Requirements 1.2, 1.6, 8.3**

- [x] 2. Create REPLBridge for REPL-specific PostMessage handling
  - [x] 2.1 Create `Common/REPLBridge.h` with class declaration
    - Define static `OnWebMessageReceived(viewer_id, json_message)` method
    - Define static `SendLanguageStatus(viewer_id, language, connected)` method
    - Define private `DispatchExec()`, `ExecWorkerThread()`, `SendResult()`, `HandleInterrupt()` methods
    - Define `REPLExecRequest` struct for worker thread parameter
    - _Requirements: 3.1, 3.2, 3.3, 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_

  - [x] 2.2 Create `Common/REPLBridge.cc` with implementation
    - Implement `OnWebMessageReceived()`: parse JSON (using json11), extract `action` field, route to handler
    - For `"repl-exec"`: validate language field against registered LanguageService names, return error for unknown languages; check `LanguageService::connected()`, return error if disconnected; call `DispatchExec()`
    - For `"repl-interrupt"`: call `HandleInterrupt()` to signal cancellation
    - Implement `DispatchExec()`: create `REPLExecRequest`, spawn worker thread via `_beginthreadex`
    - Implement `ExecWorkerThread()`: call `LanguageService::Call()` with `shell_command` field, detect content type (HTML markers, image MIME), call `SendResult()` on completion
    - Implement `SendResult()`: construct JSON response with `id`, `status`, `output`, `language`, `contentType`; post to STA thread via `ViewerManager::SendToViewer()`
    - Implement `SendLanguageStatus()`: send `repl-status` message to viewer
    - Store command in `REPLManager::AddToHistory()` after successful dispatch
    - _Requirements: 3.1, 3.2, 3.3, 3.7, 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 10.1, 10.3_

  - [ ]* 2.3 Write property tests for REPLBridge message handling
    - **Property 16: Language Validation Rejects Unknown Languages** — Generate random non-language strings, verify error response with "Unknown language: [name]"
    - **Property 8: Result Message Construction** — For any execution result with id, status, output, language, verify JSON response contains all fields correctly
    - **Validates: Requirements 9.5, 3.3, 9.3**

  - [ ]* 2.4 Write property test for content-type detection
    - **Property 17: Content-Type Detection** — Generate strings with/without HTML markers (`<html>`, `<div>`, `text/html`), verify classification as "html", "image", or "text"
    - **Validates: Requirements 10.1, 10.3**

- [x] 3. Checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Modify WindowManager to delegate to REPLManager
  - [x] 4.1 Update `Common/WindowManager.h` — remove Electron-related members
    - Remove `StartConsoleProcess()` method declaration
    - Remove `ConsoleThreadFunction()` static method
    - Remove `ShowConsoleWindowCallback()` static method
    - Remove `console_process_id_`, `console_notification_handle_`, `console_pipe_name_`, `console_notifications_` members
    - Keep `ShowConsole()`, `HideConsole()`, `ShutdownConsole()`, `SetJobHandle()`, `FocusExcelWindowCallback()`
    - _Requirements: 8.1, 8.2, 8.6_

  - [x] 4.2 Update `Common/WindowManager.cc` — redirect to REPLManager
    - `ShowConsole()`: delegate to `REPLManager::Instance().ShowConsole()`
    - `HideConsole()`: delegate to `REPLManager::Instance().HideConsole()`
    - `ShutdownConsole()`: delegate to `REPLManager::Instance().Shutdown()`
    - Remove `StartConsoleProcess()` implementation
    - Remove `ConsoleThreadFunction()` implementation
    - Remove `ShowConsoleWindowCallback()` implementation
    - Remove all Electron pipe communication code
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_

  - [ ]* 4.3 Write unit tests for WindowManager delegation
    - Test that `ShowConsole()` calls through to REPLManager
    - Test that `HideConsole()` calls through to REPLManager
    - Test that `ShutdownConsole()` calls through to REPLManager
    - _Requirements: 8.1, 8.3, 8.4_

- [x] 5. Update CMakeLists.txt and wire Core entry points
  - [x] 5.1 Update `Common/CMakeLists.txt` to include new source files
    - Add `REPLManager.cc` and `REPLBridge.cc` to `COMMON_SOURCES`
    - _Requirements: 8.5_

  - [x] 5.2 Update `Core/src/basic_functions.cc` — wire `=NEVEN.Console()` to new path
    - Ensure `RJ_Console()` function calls `WindowManager::Instance().ShowConsole()` (which now delegates to REPLManager)
    - Verify the function signature and registration remain unchanged
    - _Requirements: 8.5_

  - [x] 5.3 Update `Core/src/rj2xcl.cc` — wire shutdown in `xlAutoClose`
    - Ensure `xlAutoClose()` calls `WindowManager::Instance().ShutdownConsole()` which delegates to `REPLManager::Instance().Shutdown()`
    - _Requirements: 1.5_

- [x] 6. Checkpoint — Ensure C++ builds and tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Create the self-contained Console HTML file
  - [x] 7.1 Create `console/repl.html` — HTML structure and CSS
    - Create single self-contained HTML file with all CSS inline in `<style>` block
    - Dark theme: dark background (#1e1e1e), light text (#d4d4d4), colored prompts (blue for commands, red for errors, amber for warnings)
    - Layout: tab bar at top, output panel (scrollable) in middle, input line at bottom
    - Tab bar with R, Julia, Python tabs showing language name + connection status dot (green/red)
    - Output panel with monospace font, auto-scroll behavior
    - Input line with prompt indicator (`R>`, `julia>`, `>>>`), expandable for multi-line
    - Responsive layout that adjusts on window resize
    - Clear button per tab
    - Maximum 900x650 default viewport consideration
    - _Requirements: 7.1, 7.2, 7.3, 7.5, 2.1, 2.3, 2.7, 6.1, 6.2, 6.3, 6.4, 6.8_

  - [x] 7.2 Add JavaScript logic to `console/repl.html` — state management and message bridge
    - Implement console state object: `activeTab`, per-language `history[]`, `historyIndex`, `savedInput`, `output[]`, `executing`, `nextRequestId`
    - Implement `window.chrome.webview.postMessage()` integration for sending `repl-exec` and `repl-interrupt` messages
    - Implement incoming message handler for `repl-result` and `repl-status` actions
    - Tab switching logic: show/hide output panels, update prompt indicator, remember last active tab
    - Output rendering: append command echo with prompt prefix, render results (text/error/warning/html/image), auto-scroll unless user scrolled up
    - Output buffer management: cap at 1000 lines per tab, remove oldest DOM nodes
    - Input line: disable during execution, show spinner/pulsing prompt
    - Inline graphics: render HTML in sandboxed iframe (max 400px height, no parent access), render images as `<img>` with base64 src
    - Ctrl+C for copy support on output panel
    - Keyboard accessibility: Tab key moves focus between tab bar and input line
    - Fallback message if `window.chrome.webview` is not available
    - _Requirements: 7.4, 7.6, 7.7, 3.1, 3.4, 3.5, 3.6, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 10.2, 10.4, 10.5, 10.6_

  - [x] 7.3 Add JavaScript logic to `console/repl.html` — command history and multi-line input
    - Implement command history navigation: Up arrow shows previous, Down arrow shows next, restore saved partial input at end
    - Implement multi-line input: Shift+Enter and Ctrl+Enter insert newline, expand input area vertically (max 10 lines with scroll), show line numbers in gutter
    - Enter (without Shift) submits entire multi-line block as single execution
    - Store multi-line blocks as single history entries
    - History deduplication: skip consecutive duplicates (client-side, mirrors C++ logic)
    - History cap at 500 entries client-side
    - _Requirements: 4.1, 4.2, 4.3, 4.5, 4.6, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

  - [ ]* 7.4 Write property tests for JavaScript console state (C++ test simulating message protocol)
    - **Property 6: REPL Message Construction from Input** — Generate random non-empty strings (single and multi-line), verify `repl-exec` message contains complete text with newlines preserved and correct language
    - **Property 18: Multi-Line Block as Single History Entry** — Generate multi-line blocks (random line count), verify single history entry preserving all newlines
    - **Validates: Requirements 3.1, 5.3, 5.5**

- [x] 8. Integration wiring and ViewerWindow message routing
  - [x] 8.1 Wire REPLBridge into ViewerWindow's WebMessageReceived callback
    - In `ViewerWindow.cc`, when the viewer is the REPL console (identified by viewer_id matching `REPLManager::GetConsoleViewerId()`), route messages to `REPLBridge::OnWebMessageReceived()` instead of `PostMessageBridge::OnWebMessageReceived()`
    - Ensure non-REPL viewers continue to use the existing `PostMessageBridge`
    - _Requirements: 9.1, 9.6_

  - [x] 8.2 Wire language status notifications
    - When a `LanguageService` connection status changes, call `REPLBridge::SendLanguageStatus()` to notify the REPL console UI
    - This enables the green/red dot indicators on Language_Tabs
    - _Requirements: 2.3, 2.4, 9.4_

  - [ ]* 8.3 Write integration tests for end-to-end REPL message flow
    - Test: send `repl-exec` message → verify dispatch to mock LanguageService → verify `repl-result` posted back
    - Test: send `repl-exec` with disconnected language → verify immediate error result
    - Test: send `repl-exec` with unknown language → verify "Unknown language" error
    - _Requirements: 3.2, 3.7, 9.5_

- [x] 9. Final checkpoint — Ensure full build passes and all tests green
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- The C++ implementation language matches the existing project (C++17, MSVC 2022)
- The HTML file requires no build step — it's self-contained with inline CSS/JS
- Property tests use the existing GTest + RapidCheck infrastructure in `NEVEN/tests/`
- All code follows project conventions: `snake_case` functions, `PascalCase` classes, `.cc/.h` files
- Tests run without Excel, R, Julia, or Python (using mock infrastructure)
