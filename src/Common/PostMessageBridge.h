/**
 * Copyright (c) 2026 RJ2XCL Project — GPL v3
 *
 * @file PostMessageBridge.h
 * @brief Bidirectional communication between JavaScript (WebView2) and C++ (XLL).
 */

#pragma once

#include <string>
#include <windows.h>

namespace rj2xcl {

/**
 * @brief Handles PostMessage communication between WebView2 JavaScript and the XLL.
 *
 * JavaScript bridge (injected into every page):
 *   window.rj2xcl.sendToExcel({ action: "write-cell", sheet: "Sheet1", cell: "A1", value: 42 })
 *
 * Supported actions:
 *   - "write-cell": Write a value to a specific Excel cell
 *   - "notify": Display a message in the Excel status bar
 */
class PostMessageBridge {
public:
    /**
     * @brief Process an incoming message from JavaScript.
     * @param viewer_id The viewer that sent the message.
     * @param json_message Raw JSON string from window.chrome.webview.postMessage.
     * @param application_dispatch Excel COM dispatch pointer.
     */
    static void OnWebMessageReceived(
        const std::string& viewer_id,
        const std::string& json_message,
        LPDISPATCH application_dispatch);

    /**
     * @brief Get the JavaScript bridge code to inject into pages.
     * @return JavaScript source code string.
     */
    static const char* GetBridgeScript();

private:
    static void HandleWriteCell(const std::string& sheet, const std::string& cell,
                                 const std::string& value, LPDISPATCH application_dispatch);
    static void HandleNotify(const std::string& message, LPDISPATCH application_dispatch);
    static void HandleSaveRequest(const std::string& viewer_id);
};

} // namespace rj2xcl
