# Requirements Document

## Introduction

Este documento especifica los requerimientos para una consola REPL (Read-Eval-Print Loop) interactiva que reemplaza la consola Electron obsoleta (Electron 1.8, 2018, xterm.js + Monaco) con una implementación ligera que corre dentro del subsistema WebView2 existente de NEVEN. La consola permite ejecutar código R, Julia y Python de forma interactiva desde una ventana embebida en Excel, sin dependencias externas (sin Node.js, sin npm, sin Electron).

La consola REPL se integra con la infraestructura existente:
- **ViewerManager** crea y gestiona la ventana WebView2 en el STA thread dedicado.
- **PostMessageBridge** proporciona comunicación bidireccional JS↔C++ via `window.chrome.webview.postMessage()` y `ICoreWebView2::PostWebMessageAsJson`.
- **LanguageManager** despacha la ejecución de código a los procesos hijo (ControlR.exe, ControlJulia.exe, ControlPython.exe) via Named Pipes + Protobuf.
- La función existente `=NEVEN.Console()` invoca `ShowConsole()` en WindowManager — esta se redirige al nuevo REPL WebView2.

La UI es HTML/CSS/JS puro servido al WebView2, con tabs para cambiar entre lenguajes, historial de comandos, y soporte para salida multi-línea con formato (texto, errores, gráficos inline).

## Glossary

- **REPL_Console**: La ventana WebView2 que hospeda la interfaz de consola interactiva HTML/CSS/JS, permitiendo al usuario escribir y ejecutar código en R, Julia o Python.
- **REPL_Bridge**: La extensión del PostMessage_Bridge que maneja mensajes específicos de la consola REPL, incluyendo envío de código para ejecución y recepción de resultados.
- **Language_Tab**: Un tab en la interfaz de la consola que representa una sesión activa para un lenguaje específico (R, Julia, o Python), con su propio historial y estado.
- **Command_History**: La lista ordenada de comandos previamente ejecutados por el usuario en una Language_Tab específica, navegable con las teclas flecha arriba/abajo.
- **Output_Panel**: El área de la consola donde se muestran los resultados de ejecución, mensajes de error, y salida estándar del lenguaje activo.
- **Input_Line**: El campo de entrada de texto en la parte inferior de la consola donde el usuario escribe comandos para ejecutar.
- **Shell_Exec**: El modo de ejecución interactiva en los procesos hijo (RShellExec, JuliaShellExec, PythonShellExec) que evalúa expresiones y retorna resultados formateados como en un REPL nativo.
- **ViewerManager**: El singleton existente que gestiona ventanas WebView2 en un STA thread dedicado.
- **PostMessage_Bridge**: El mecanismo existente de comunicación bidireccional entre JavaScript (WebView2) y C++ (XLL).
- **LanguageManager**: El registro singleton que gestiona los servicios de lenguaje y despacha llamadas a los procesos hijo.
- **LanguageService**: La clase base abstracta que representa un servicio de lenguaje conectado via Named Pipe, con método `Call()` para ejecutar código.
- **Console_HTML**: El archivo HTML autocontenido (con CSS y JS inline) que implementa la interfaz de la consola REPL, servido al WebView2 via `NavigateToString`.
- **Prompt_Indicator**: El indicador visual en la Input_Line que muestra el lenguaje activo (e.g., `R>`, `julia>`, `>>>` para Python).
- **Multi_Line_Mode**: El modo de entrada que permite al usuario escribir bloques de código de múltiples líneas antes de enviarlos para ejecución (activado con Shift+Enter).
- **WindowManager**: El componente existente que gestiona la consola Electron legacy — será modificado para redirigir al nuevo REPL WebView2.

## Requirements

### Requirement 1: Console Window Lifecycle

**User Story:** As an Excel user, I want to open an interactive REPL console from Excel, so that I can execute R, Julia, and Python code interactively without leaving the Excel environment.

#### Acceptance Criteria

1. WHEN the user calls `=NEVEN.Console()`, THE REPL_Console SHALL open a WebView2 Viewer_Window with the Console_HTML loaded via `NavigateToString`.
2. WHEN the REPL_Console is already open and the user calls `=NEVEN.Console()` again, THE ViewerManager SHALL bring the existing REPL_Console window to the foreground instead of creating a new instance.
3. THE REPL_Console window SHALL have a default size of 900 pixels wide by 650 pixels tall, and SHALL be resizable by the user.
4. WHEN the user closes the REPL_Console window via the close button, THE ViewerManager SHALL destroy the WebView2 controller and release resources, but SHALL preserve the Command_History in memory for the session.
5. WHEN Excel is closed (xlAutoClose), THE REPL_Console SHALL be closed and all associated resources SHALL be released.
6. THE REPL_Console SHALL be a singleton instance — only one REPL_Console window SHALL exist at any time within the Excel session.
7. IF the ViewerManager availability status is false (WebView2 not installed), THEN `=NEVEN.Console()` SHALL return the error string "WebView2 not available — install Edge WebView2 Runtime".

### Requirement 2: Language Tab Interface

**User Story:** As an Excel user, I want to switch between R, Julia, and Python sessions using tabs, so that I can work with multiple languages in the same console window.

#### Acceptance Criteria

1. THE REPL_Console SHALL display a tab bar at the top with one Language_Tab for each connected language service (R, Julia, Python).
2. WHEN the user clicks a Language_Tab, THE REPL_Console SHALL switch the visible Output_Panel and Input_Line to the selected language session.
3. EACH Language_Tab SHALL display the language name and a visual indicator of connection status: green dot for connected, red dot for disconnected.
4. WHEN a language service is not connected (LanguageService.connected() returns false), THE Language_Tab SHALL be visible but disabled, and clicking it SHALL display the message "Language not available — engine not connected" in the Output_Panel.
5. THE REPL_Console SHALL remember the last active Language_Tab and restore it when the console is reopened within the same Excel session.
6. EACH Language_Tab SHALL maintain its own independent Command_History and Output_Panel content.
7. THE Prompt_Indicator SHALL display `R>` for R, `julia>` for Julia, and `>>>` for Python, matching the native REPL prompts of each language.

### Requirement 3: Code Execution via PostMessage Bridge

**User Story:** As an Excel user, I want to type code in the console and see results immediately, so that I can interactively explore data and test expressions.

#### Acceptance Criteria

1. WHEN the user presses Enter in the Input_Line, THE REPL_Console JavaScript SHALL send a PostMessage to C++ with the action `"repl-exec"`, the language identifier, and the code string.
2. WHEN the REPL_Bridge receives a `"repl-exec"` message, THE XLL SHALL dispatch the code to the appropriate LanguageService using the Shell_Exec mode (RShellExec, JuliaShellExec, or PythonShellExec).
3. WHEN the LanguageService returns a result, THE REPL_Bridge SHALL send the result back to the REPL_Console JavaScript via `PostWebMessageAsJson` with the action `"repl-result"`, including the output text and a status field ("ok" or "error").
4. WHEN the REPL_Console JavaScript receives a `"repl-result"` message with status "ok", THE Output_Panel SHALL append the result text formatted as standard output (monospace font, default text color).
5. WHEN the REPL_Console JavaScript receives a `"repl-result"` message with status "error", THE Output_Panel SHALL append the error text formatted with a red color and an error prefix.
6. WHILE a command is executing, THE Input_Line SHALL be disabled and THE REPL_Console SHALL display a visual indicator (spinner or pulsing prompt) to show that execution is in progress.
7. IF the LanguageService is not connected when a `"repl-exec"` message is received, THEN THE REPL_Bridge SHALL immediately return a `"repl-result"` with status "error" and the message "Language engine not connected".

### Requirement 4: Command History

**User Story:** As an Excel user, I want to navigate through previously executed commands using arrow keys, so that I can quickly re-execute or modify past commands.

#### Acceptance Criteria

1. WHEN the user presses the Up Arrow key in the Input_Line, THE REPL_Console SHALL replace the current input text with the previous command from the Command_History for the active Language_Tab.
2. WHEN the user presses the Down Arrow key in the Input_Line, THE REPL_Console SHALL replace the current input text with the next command from the Command_History, or clear the input if at the end of history.
3. THE Command_History SHALL store up to 500 commands per Language_Tab, discarding the oldest commands when the limit is reached.
4. THE Command_History SHALL persist across console close/reopen within the same Excel session (stored in C++ memory, not on disk).
5. WHEN the user presses Up Arrow with a partially typed command in the Input_Line, THE REPL_Console SHALL save the partial input and restore it when the user navigates back to the end of history.
6. THE Command_History SHALL not store duplicate consecutive commands (if the same command is executed twice in a row, it SHALL appear only once in history).

### Requirement 5: Multi-Line Input

**User Story:** As an Excel user, I want to enter multi-line code blocks (function definitions, loops, conditionals), so that I can write complex code interactively.

#### Acceptance Criteria

1. WHEN the user presses Shift+Enter in the Input_Line, THE REPL_Console SHALL insert a newline character and expand the Input_Line vertically to show the additional line, without executing the code.
2. WHEN the Input_Line contains multiple lines, THE REPL_Console SHALL display line numbers in a gutter on the left side of the input area.
3. WHEN the user presses Enter (without Shift) in a multi-line Input_Line, THE REPL_Console SHALL send the entire multi-line block as a single execution unit to the REPL_Bridge.
4. THE Input_Line SHALL support a maximum height of 10 visible lines, with vertical scrolling enabled when the content exceeds this limit.
5. WHEN a multi-line block is executed, THE Command_History SHALL store the entire block as a single history entry.
6. THE Input_Line SHALL support Ctrl+Enter as an alternative to Shift+Enter for inserting newlines, providing consistency with common code editor conventions.

### Requirement 6: Output Formatting and Display

**User Story:** As an Excel user, I want the console output to be clearly formatted with syntax highlighting for errors and distinct visual separation between commands and results, so that I can easily read and understand the output.

#### Acceptance Criteria

1. THE Output_Panel SHALL display executed commands prefixed with the Prompt_Indicator (e.g., `R> summary(x)`) in a distinct color (blue) to differentiate them from output.
2. THE Output_Panel SHALL display standard output in the default monospace font color (light gray on dark background or dark gray on light background).
3. THE Output_Panel SHALL display error messages in red with a bold prefix indicating the error source (e.g., "Error in R:" or "Julia ERROR:").
4. THE Output_Panel SHALL display warning messages in yellow/amber color.
5. THE Output_Panel SHALL auto-scroll to the bottom when new output is appended, unless the user has manually scrolled up to review previous output.
6. THE Output_Panel SHALL support selecting and copying text via standard Ctrl+C keyboard shortcut.
7. WHEN the output contains more than 1000 lines for a single Language_Tab, THE Output_Panel SHALL remove the oldest lines to maintain a maximum buffer of 1000 lines, preserving the most recent output.
8. THE REPL_Console SHALL provide a "Clear" button per Language_Tab that clears the Output_Panel content without affecting the Command_History.

### Requirement 7: Console HTML/CSS/JS Implementation

**User Story:** As a developer maintaining NEVEN, I want the console UI to be a single self-contained HTML file with no external dependencies, so that it can be served directly to WebView2 without a build system or package manager.

#### Acceptance Criteria

1. THE Console_HTML SHALL be a single HTML file containing all CSS and JavaScript inline (no external file references, no CDN links, no npm packages).
2. THE Console_HTML SHALL use a dark theme by default with a color scheme consistent with modern terminal emulators (dark background, light text, colored prompts).
3. THE Console_HTML SHALL be responsive, adjusting its layout when the REPL_Console window is resized by the user.
4. THE Console_HTML SHALL use the `window.chrome.webview.postMessage()` API for all communication with the C++ backend, via the `window.neven` bridge object.
5. THE Console_HTML SHALL implement keyboard accessibility: Tab key SHALL move focus between the tab bar and the Input_Line, and all interactive elements SHALL be reachable via keyboard navigation.
6. THE Console_HTML file SHALL be stored at `%NEVEN_HOME%/console/repl.html` and loaded by the ViewerManager when the REPL_Console is opened.
7. THE Console_HTML SHALL render correctly in the WebView2 Chromium engine without requiring any polyfills or compatibility shims.

### Requirement 8: Integration with Existing WindowManager

**User Story:** As a developer maintaining NEVEN, I want the new REPL console to replace the old Electron console seamlessly, so that existing code paths (`=NEVEN.Console()`, `ShowConsole()`) work without modification to the user-facing API.

#### Acceptance Criteria

1. WHEN `ShowConsole()` is called on WindowManager, THE WindowManager SHALL delegate to the ViewerManager to open the REPL_Console instead of launching the Electron process.
2. THE WindowManager SHALL no longer launch `rj2xcl-console.exe` (the Electron process) — the `StartConsoleProcess` method SHALL be deprecated and replaced with a call to the ViewerManager.
3. WHEN the REPL_Console is open and `ShowConsole()` is called, THE WindowManager SHALL bring the existing REPL_Console window to the foreground.
4. WHEN the REPL_Console is open and `HideConsole()` is called, THE WindowManager SHALL hide the REPL_Console window and return focus to Excel.
5. THE existing `=NEVEN.Console()` Excel function SHALL continue to work without changes to its signature or registration — only the internal implementation changes.
6. THE old Electron console pipe communication (ConsoleThreadFunction, console_pipe_name_, console_notifications_) SHALL be removed from WindowManager as dead code.

### Requirement 9: REPL Bridge Extension to PostMessageBridge

**User Story:** As a developer maintaining NEVEN, I want the PostMessage bridge to handle REPL-specific messages, so that the console can communicate with language engines through the existing WebView2 infrastructure.

#### Acceptance Criteria

1. THE REPL_Bridge SHALL handle the action `"repl-exec"` with JSON fields: `language` (string: "R", "Julia", or "Python"), `code` (string: the code to execute), and `id` (integer: unique request identifier for correlating responses).
2. THE REPL_Bridge SHALL handle the action `"repl-interrupt"` with JSON field `language` (string) to request cancellation of a running command in the specified language engine.
3. THE REPL_Bridge SHALL send responses to the REPL_Console with the action `"repl-result"` containing fields: `id` (integer: matching request id), `status` (string: "ok" or "error"), `output` (string: the result text), and `language` (string: the source language).
4. THE REPL_Bridge SHALL send the action `"repl-status"` to the REPL_Console when a language service connection status changes, containing fields: `language` (string) and `connected` (boolean).
5. THE REPL_Bridge SHALL validate that the `language` field in `"repl-exec"` messages matches a registered LanguageService name before dispatching execution. IF the language is not recognized, THEN THE REPL_Bridge SHALL return a `"repl-result"` with status "error" and the message "Unknown language: [name]".
6. THE REPL_Bridge SHALL execute code asynchronously — dispatching to the LanguageService on a worker thread and posting the result back to the STA thread for delivery to WebView2.

### Requirement 10: Inline Graphics Support

**User Story:** As an Excel user, I want R and Julia plots generated in the REPL to appear inline in the console output, so that I can see visualizations alongside my code without opening separate windows.

#### Acceptance Criteria

1. WHEN a Shell_Exec command produces HTML output (detected by the `text/html` MIME type or HTML content markers), THE REPL_Bridge SHALL send a `"repl-result"` with an additional field `contentType` set to "html".
2. WHEN the REPL_Console JavaScript receives a `"repl-result"` with `contentType` "html", THE Output_Panel SHALL render the HTML content in a sandboxed iframe element with a maximum height of 400 pixels.
3. WHEN a Shell_Exec command produces a PNG or SVG image (detected by MIME type), THE REPL_Bridge SHALL encode the image as a base64 data URI and send it in the `output` field with `contentType` set to "image".
4. WHEN the REPL_Console JavaScript receives a `"repl-result"` with `contentType` "image", THE Output_Panel SHALL display the image inline with a maximum width of 100% of the Output_Panel width and a maximum height of 400 pixels.
5. THE inline graphics SHALL be non-interactive (static rendering) — for interactive visualizations, the user SHALL use the existing `=NEVEN.View()` function which opens a dedicated Viewer_Window.
6. WHEN inline HTML content contains `<script>` tags, THE sandboxed iframe SHALL execute the scripts in isolation without access to the parent REPL_Console document or the `window.neven` bridge.

