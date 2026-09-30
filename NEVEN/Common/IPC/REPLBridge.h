/**
 * Copyright (c) 2026 RJ2XCL Project — GPL v3
 *
 * @file REPLBridge.h
 * @brief REPL-specific PostMessage bridge for the WebView2 console.
 *
 * Handles REPL message actions (repl-exec, repl-interrupt, repl-result,
 * repl-status) between the console JavaScript and the C++ language engines.
 */

#pragma once

#include <string>
#include <vector>
#include <windows.h>

namespace rj2xcl {

struct DiagnosticMessage;  // Forward declaration

/**
 * @brief Worker thread parameter for asynchronous code execution.
 */
struct REPLExecRequest {
    std::string viewer_id;
    std::string language;
    std::string code;
    int request_id;
};

/**
 * @brief Handles REPL-specific PostMessage communication.
 *
 * Routes incoming messages from the REPL console JavaScript to the
 * appropriate language engine, and sends results back via PostWebMessage.
 * Code execution is dispatched to a worker thread to avoid blocking
 * the STA thread or the WebView2 message pump.
 */
class REPLBridge {
public:
    /**
     * @brief Process an incoming REPL message from JavaScript.
     * Called on the STA thread by ViewerWindow's WebMessageReceived handler.
     * @param viewer_id The viewer that sent the message.
     * @param json_message Raw JSON string from window.chrome.webview.postMessage.
     */
    static void OnWebMessageReceived(
        const std::string& viewer_id,
        const std::string& json_message);

    /**
     * @brief Send a language connection status update to the REPL console.
     * @param viewer_id Target viewer.
     * @param language Language name ("R", "Julia", "Python").
     * @param connected Whether the language service is connected.
     */
    static void SendLanguageStatus(
        const std::string& viewer_id,
        const std::string& language,
        bool connected);

    /**
     * @brief Send a diagnostic message to the REPL console.
     * Called from STA thread (via DiagnosticRouter::DeliverPending).
     * @param viewer_id Target viewer.
     * @param language Source language ("R", "Julia", "Python").
     * @param type Message type ("output" or "warning").
     * @param text Message content.
     * @param timestamp Milliseconds since epoch.
     */
    static void SendDiagnostic(
        const std::string& viewer_id,
        const std::string& language,
        const std::string& type,
        const std::string& text,
        int64_t timestamp);

    /**
     * @brief Send multiple buffered diagnostics at once (batch delivery on console open).
     * @param viewer_id Target viewer.
     * @param messages Vector of diagnostic messages to send.
     */
    static void SendDiagnosticBatch(
        const std::string& viewer_id,
        const std::vector<DiagnosticMessage>& messages);

private:
    /**
     * @brief Dispatch code execution to a worker thread.
     * @param viewer_id Target viewer for result delivery.
     * @param language Language to execute in.
     * @param code Code string to execute.
     * @param request_id Unique request ID for correlating responses.
     */
    static void DispatchExec(
        const std::string& viewer_id,
        const std::string& language,
        const std::string& code,
        int request_id);

    /**
     * @brief Worker thread function for code execution.
     * @param param Pointer to a heap-allocated REPLExecRequest.
     * @return Thread exit code (always 0).
     */
    static unsigned __stdcall ExecWorkerThread(void* param);

    /**
     * @brief Send execution result back to the REPL console.
     * @param viewer_id Target viewer.
     * @param request_id Matching request ID.
     * @param status "ok" or "error".
     * @param output Result text.
     * @param language Source language.
     * @param content_type "text", "html", or "image".
     */
    static void SendResult(
        const std::string& viewer_id,
        int request_id,
        const std::string& status,
        const std::string& output,
        const std::string& language,
        const std::string& content_type = "text");

    /**
     * @brief Handle interrupt request for a running command.
     * @param language Language to interrupt.
     */
    static void HandleInterrupt(const std::string& language);

    /**
     * @brief Detect content type from execution output.
     * @param output The output string to analyze.
     * @return "html", "image", or "text".
     */
    static std::string DetectContentType(const std::string& output);
};

} // namespace rj2xcl
