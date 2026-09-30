# Requirements Document

## Introduction

Este documento especifica los requerimientos para un flujo de mensajes diagnósticos (diagnostic stream) que permite a la consola REPL de NEVEN mostrar mensajes de stdout/stderr, warnings y mensajes de carga de paquetes que R, Julia y Python emiten durante la ejecución de funciones desde **celdas de Excel** (no solo desde el REPL interactivo).

Actualmente, cuando una función como `=R.MR_Lineal(...)` se ejecuta en una celda, R puede emitir warnings ("Warning: NAs introduced by coercion"), mensajes informativos ("Loading required package: MASS"), o errores parciales que se pierden porque no hay un destino visible para ellos. Este feature convierte la consola REPL en un **panel diagnóstico** que captura y muestra estos mensajes en tiempo real, ayudando al usuario a depurar sus scripts sin necesidad de herramientas externas.

La arquitectura existente ya tiene los mecanismos base:
- **R**: `R_WriteConsoleEx` en ControlR.exe captura stdout/stderr y los envía como mensajes `Console` (protobuf) por el callback pipe (`RJ2XCL2-PIPE-R-{PID}-CB`).
- **Julia**: ControlJulia.exe tiene un callback pipe similar con `PushConsoleMessage`.
- **Python**: ControlPython.exe NO tiene callback pipe activo (deshabilitado por bug de timing), pero puede capturar stdout/stderr via redirección de `sys.stdout`/`sys.stderr` en `startup.py`.

El desafío principal es que el callback pipe actualmente se usa para COM automation (bidireccional con `call.wait()`), y los mensajes de consola deben diferenciarse de los callbacks COM. Además, los mensajes deben fluir en tiempo real sin bloquear el thread principal de Excel.

## Glossary

- **Diagnostic_Stream**: El flujo unidireccional de mensajes (stdout, stderr, warnings) desde los procesos hijo (ControlR, ControlJulia, ControlPython) hacia la consola REPL, generados durante la ejecución de funciones desde celdas de Excel.
- **Cell_Execution**: La ejecución de una función de lenguaje (R, Julia, Python) invocada desde una celda de Excel (e.g., `=R.MR_Lineal(...)`), en contraste con la ejecución interactiva desde el REPL.
- **Callback_Pipe**: El Named Pipe dedicado (`RJ2XCL2-PIPE-{LANG}-{PID}-CB`) que los procesos hijo usan para enviar mensajes asíncronos de vuelta al XLL. Actualmente maneja COM callbacks, graphics device updates y function list updates.
- **Console_Message**: Un mensaje protobuf de tipo `Console` (definido en `variable.proto`) que contiene texto (`text`), error (`err`), prompt (`prompt`), o datos gráficos (`graphics`).
- **Diagnostic_Router**: El componente en el XLL que recibe Console_Messages del Callback_Pipe y los enruta hacia la consola REPL via el REPLBridge, diferenciándolos de los COM callbacks.
- **Output_Buffer**: Un buffer circular en el XLL que almacena mensajes diagnósticos cuando la consola REPL no está abierta, para entregarlos cuando el usuario la abra.
- **REPL_Console**: La ventana WebView2 que hospeda la interfaz de consola interactiva (ya implementada en el spec webview2-repl-console).
- **REPLBridge**: La clase C++ que maneja la comunicación PostMessage entre el WebView2 y el XLL para la consola REPL.
- **ViewerManager**: El singleton que gestiona ventanas WebView2 en un STA thread dedicado.
- **LanguageService**: La clase que representa un servicio de lenguaje conectado via Named Pipe, con su RunCallbackThread dedicado.
- **Python_Diagnostic_Buffer**: Un buffer en el proceso ControlPython que acumula mensajes de stdout/stderr capturados via redirección de `sys.stdout`/`sys.stderr`, y los entrega al XLL cuando se solicitan via el pipe principal.
- **Message_Source**: El identificador de origen de un mensaje diagnóstico, indicando si proviene de una Cell_Execution o de una ejecución REPL interactiva.

## Requirements

### Requirement 1: Capture and Route R Diagnostic Messages from Cell Execution

**User Story:** As an Excel user, I want to see R warnings, messages, and errors that occur during cell function execution in the REPL console, so that I can debug issues with my R formulas without guessing what went wrong.

#### Acceptance Criteria

1. WHEN R emits a stdout message (via `R_WriteConsoleEx` with flag=0) during a Cell_Execution, THE Diagnostic_Router SHALL forward the Console_Message to the REPL_Console as a diagnostic entry with type "output" and source language "R".
2. WHEN R emits a stderr message (via `R_WriteConsoleEx` with flag=1) during a Cell_Execution, THE Diagnostic_Router SHALL forward the Console_Message to the REPL_Console as a diagnostic entry with type "warning" and source language "R".
3. WHEN the Callback_Pipe receives a Console_Message (protobuf `CallResponse` with `operation_case() == kConsole`), THE Diagnostic_Router SHALL differentiate the message from COM callbacks by checking the operation case and SHALL NOT invoke the COM automation path for console messages.
4. THE Diagnostic_Router SHALL forward Console_Messages to the REPL_Console within 100 milliseconds of receiving them from the Callback_Pipe, without blocking the Excel main thread.
5. WHEN multiple Console_Messages arrive in rapid succession (e.g., R printing a multi-line warning), THE Diagnostic_Router SHALL deliver each message individually in the order received, preserving the original sequence.

### Requirement 2: Capture and Route Julia Diagnostic Messages from Cell Execution

**User Story:** As an Excel user, I want to see Julia stdout/stderr output from cell function execution in the REPL console, so that I can monitor package loading messages and runtime warnings.

#### Acceptance Criteria

1. WHEN Julia emits a stdout message during a Cell_Execution, THE Diagnostic_Router SHALL forward the message to the REPL_Console as a diagnostic entry with type "output" and source language "Julia".
2. WHEN Julia emits a stderr message during a Cell_Execution, THE Diagnostic_Router SHALL forward the message to the REPL_Console as a diagnostic entry with type "warning" and source language "Julia".
3. THE ControlJulia process SHALL send stdout/stderr messages as protobuf Console_Messages via the Callback_Pipe, using the same `PushConsoleMessage` mechanism already used for prompt messages.

### Requirement 3: Capture and Route Python Diagnostic Messages from Cell Execution

**User Story:** As an Excel user, I want to see Python stdout/stderr output from cell function execution in the REPL console, so that I can see print statements and error tracebacks from my Python functions.

#### Acceptance Criteria

1. WHEN Python emits a stdout message during a Cell_Execution, THE Python_Diagnostic_Buffer SHALL capture the message via the redirected `sys.stdout`.
2. WHEN Python emits a stderr message during a Cell_Execution, THE Python_Diagnostic_Buffer SHALL capture the message via the redirected `sys.stderr`.
3. WHEN a Python Cell_Execution completes, THE ControlPython process SHALL send accumulated Python_Diagnostic_Buffer contents to the XLL as part of the function response, using a dedicated field in the protobuf response.
4. WHEN the XLL receives a Python function response containing diagnostic messages, THE Diagnostic_Router SHALL forward those messages to the REPL_Console as diagnostic entries with source language "Python".
5. IF the Python_Diagnostic_Buffer exceeds 64 KB during a single Cell_Execution, THEN THE Python_Diagnostic_Buffer SHALL truncate the oldest messages and append a truncation indicator "[...truncated...]".

### Requirement 4: Diagnostic Message Display in REPL Console

**User Story:** As an Excel user, I want diagnostic messages from cell executions to be visually distinct from REPL interactive output, so that I can easily distinguish between my interactive commands and background cell diagnostics.

#### Acceptance Criteria

1. THE REPL_Console SHALL display diagnostic messages from Cell_Executions with a visual prefix indicating the source: `[R]`, `[Julia]`, or `[Python]` followed by the message text.
2. THE REPL_Console SHALL display diagnostic messages with a distinct visual style: a left border or background tint that differentiates them from interactive REPL output.
3. WHEN a diagnostic message has type "warning", THE REPL_Console SHALL display the message in amber/yellow color, consistent with the existing warning style.
4. WHEN a diagnostic message has type "output", THE REPL_Console SHALL display the message in a muted/secondary text color to avoid visual noise.
5. THE REPL_Console SHALL display diagnostic messages in the Output_Panel of the corresponding Language_Tab (R messages in the R tab, Julia messages in the Julia tab, Python messages in the Python tab).
6. WHEN the user is viewing a different Language_Tab than the one receiving diagnostic messages, THE REPL_Console SHALL display a notification badge (unread count) on the tab receiving messages.
7. THE REPL_Console SHALL append diagnostic messages to the Output_Panel in chronological order, interleaved with any interactive REPL output that occurs simultaneously.

### Requirement 5: Diagnostic Stream Protocol (C++ to JavaScript)

**User Story:** As a developer maintaining NEVEN, I want a well-defined message protocol for diagnostic messages between C++ and the console JavaScript, so that the diagnostic stream integrates cleanly with the existing REPL message protocol.

#### Acceptance Criteria

1. THE REPLBridge SHALL send diagnostic messages to the REPL_Console JavaScript using the action `"diagnostic"` with JSON fields: `language` (string: "R", "Julia", or "Python"), `type` (string: "output" or "warning"), `text` (string: the message content), and `timestamp` (integer: milliseconds since epoch).
2. THE REPLBridge SHALL send diagnostic messages via the same `PostWebMessageAsJson` mechanism used for `"repl-result"` messages, ensuring delivery on the STA thread.
3. WHEN the REPL_Console is not open (no active viewer), THE Diagnostic_Router SHALL buffer diagnostic messages in the Output_Buffer up to a maximum of 200 messages.
4. WHEN the REPL_Console is opened and the Output_Buffer contains buffered messages, THE Diagnostic_Router SHALL deliver all buffered messages to the console in chronological order within 500 milliseconds of the console becoming ready.
5. THE diagnostic message protocol SHALL NOT interfere with existing `"repl-result"` and `"repl-status"` messages — both streams SHALL coexist independently.

### Requirement 6: Diagnostic Router Integration with Callback Pipe

**User Story:** As a developer maintaining NEVEN, I want the diagnostic router to correctly differentiate console messages from COM callbacks on the callback pipe, so that existing COM automation functionality is not disrupted.

#### Acceptance Criteria

1. WHEN the Callback_Pipe receives a `CallResponse` with `operation_case() == kConsole`, THE Diagnostic_Router SHALL handle the message as a diagnostic message and SHALL NOT pass it to `HandleCallback` or the COM automation path.
2. WHEN the Callback_Pipe receives a `CallResponse` with `operation_case() == kFunctionCall`, THE existing HandleCallback logic SHALL process the message unchanged, preserving COM automation, graphics device, and function list update functionality.
3. THE Diagnostic_Router SHALL operate on the RunCallbackThread (the dedicated callback pipe thread per language), forwarding messages to the REPLBridge without requiring thread synchronization with the Excel main thread.
4. IF the Diagnostic_Router encounters a malformed Console_Message (empty text and empty err fields), THEN THE Diagnostic_Router SHALL discard the message and log a warning, without affecting subsequent message processing.
5. THE Diagnostic_Router SHALL NOT send a response back on the Callback_Pipe for Console_Messages (they are fire-and-forget, unlike COM callbacks which require `call.wait()` responses).

### Requirement 7: Output Buffer for Offline Console

**User Story:** As an Excel user, I want diagnostic messages to be preserved even when the console is closed, so that when I open the console I can see recent warnings from cell executions that happened while the console was closed.

#### Acceptance Criteria

1. THE Output_Buffer SHALL store up to 200 diagnostic messages per language (600 total across R, Julia, Python) when the REPL_Console is not open.
2. WHEN the Output_Buffer reaches its capacity for a language, THE Output_Buffer SHALL discard the oldest message for that language to make room for the new message (FIFO eviction).
3. WHEN the REPL_Console is opened, THE Output_Buffer SHALL deliver all buffered messages to the console and clear the buffer.
4. THE Output_Buffer SHALL persist across console close/reopen cycles within the same Excel session (stored in C++ memory).
5. WHEN Excel is closed (xlAutoClose), THE Output_Buffer SHALL be released without persisting to disk.

### Requirement 8: Console Toggle for Diagnostic Stream

**User Story:** As an Excel user, I want to enable or disable the diagnostic stream display in the console, so that I can focus on interactive work without being distracted by background messages when I don't need them.

#### Acceptance Criteria

1. THE REPL_Console SHALL provide a toggle button (or checkbox) in the tab bar area labeled "Diagnostics" that enables or disables the display of diagnostic messages.
2. WHEN the diagnostics toggle is disabled, THE REPL_Console SHALL hide all diagnostic messages from the Output_Panel but SHALL continue buffering them in the Output_Buffer.
3. WHEN the diagnostics toggle is re-enabled, THE REPL_Console SHALL display all buffered diagnostic messages that were received while the toggle was disabled.
4. THE diagnostics toggle state SHALL default to enabled (showing diagnostic messages).
5. THE diagnostics toggle state SHALL persist across console close/reopen within the same Excel session.

### Requirement 9: Thread Safety for Diagnostic Message Delivery

**User Story:** As a developer maintaining NEVEN, I want the diagnostic message delivery to be thread-safe, so that concurrent cell executions across multiple languages do not cause data races or message corruption.

#### Acceptance Criteria

1. THE Diagnostic_Router SHALL use a thread-safe queue (mutex-protected or lock-free) to transfer messages from the RunCallbackThread to the STA thread where PostWebMessage is called.
2. WHEN multiple languages emit diagnostic messages simultaneously (e.g., R and Julia executing concurrently), THE Diagnostic_Router SHALL deliver messages from each language independently without blocking one language's delivery on another.
3. THE Output_Buffer SHALL be protected by a mutex to allow safe concurrent access from multiple RunCallbackThreads (one per language) and the STA thread (for delivery to WebView2).
4. THE Diagnostic_Router SHALL NOT hold any lock while calling PostWebMessageAsJson, to avoid potential deadlocks with the WebView2 message pump.

### Requirement 10: Diagnostic Message Filtering by Severity

**User Story:** As an Excel user, I want to filter diagnostic messages by severity (stdout vs stderr/warnings), so that I can focus on errors and warnings without being overwhelmed by informational output.

#### Acceptance Criteria

1. THE REPL_Console SHALL provide filter controls that allow the user to show or hide messages by type: "output" (stdout) and "warning" (stderr/warnings).
2. WHEN the "output" filter is disabled, THE REPL_Console SHALL hide diagnostic messages of type "output" while continuing to display messages of type "warning".
3. WHEN the "warning" filter is disabled, THE REPL_Console SHALL hide diagnostic messages of type "warning" while continuing to display messages of type "output".
4. THE filter state SHALL apply per-session and default to showing all message types.
5. WHEN a filter is toggled, THE REPL_Console SHALL immediately update the visible messages in the Output_Panel without requiring a page reload.
