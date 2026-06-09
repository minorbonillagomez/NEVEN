/**
 * Copyright (c) 2026 RJ2XCL Project — GPL v3
 *
 * @file PostMessageBridge.cc
 * @brief Implementation of the JavaScript ↔ C++ PostMessage bridge.
 */

#include "PostMessageBridge.h"
#include "LogService.h"
#include "ViewerManager.h"
#include "ViewerWindow.h"
#include "json11/json11.hpp"

#include <commdlg.h>
#include <fstream>

// WM_APP message for save operations (must match ViewerManager.cc)
static constexpr UINT WM_APP_SAVE_CONTENT = WM_APP + 105;

// Save request struct (must match ViewerManager.cc)
struct SaveContentRequest {
    std::string viewer_id;
    std::string file_path;
    std::string format;  // "html", "png", "pdf"
};

namespace rj2xcl {

void PostMessageBridge::OnWebMessageReceived(
    const std::string& viewer_id,
    const std::string& json_message,
    LPDISPATCH application_dispatch)
{
    // Parse JSON
    std::string err;
    json11::Json msg = json11::Json::parse(json_message, err);

    if (!err.empty()) {
        RJ2XCL_LOG_WARN("PostMessageBridge: invalid JSON from %s: %s",
                         viewer_id.c_str(), err.c_str());
        return;
    }

    std::string action = msg["action"].string_value();

    if (action == "write-cell") {
        std::string sheet = msg["sheet"].string_value();
        std::string cell = msg["cell"].string_value();
        std::string value;

        if (msg["value"].is_number()) {
            value = std::to_string(msg["value"].number_value());
        } else {
            value = msg["value"].string_value();
        }

        if (sheet.empty() || cell.empty()) {
            RJ2XCL_LOG_WARN("PostMessageBridge: write-cell missing sheet or cell reference");
            return;
        }

        HandleWriteCell(sheet, cell, value, application_dispatch);

    } else if (action == "notify") {
        std::string message = msg["message"].string_value();
        if (!message.empty()) {
            HandleNotify(message, application_dispatch);
        }

    } else if (action == "save-request") {
        HandleSaveRequest(viewer_id);

    } else {
        RJ2XCL_LOG_WARN("PostMessageBridge: unrecognized action '%s' from %s",
                         action.c_str(), viewer_id.c_str());
    }
}

const char* PostMessageBridge::GetBridgeScript() {
    return R"(
        window.neven = {
            sendToExcel: function(data) {
                window.chrome.webview.postMessage(JSON.stringify(data));
            },
            version: '2.0'
        };
        window.rj2xcl = window.neven;
    )";
}

void PostMessageBridge::HandleWriteCell(const std::string& sheet, const std::string& cell,
                                         const std::string& value, LPDISPATCH application_dispatch)
{
    // Write-cell requires COM automation marshalling which is complex from the STA thread.
    // For now, log the request. Full implementation requires AtlUnmarshalPtr on the UI thread.
    RJ2XCL_LOG_INFO("PostMessageBridge: write-cell %s!%s = %s", sheet.c_str(), cell.c_str(), value.c_str());
}

void PostMessageBridge::HandleNotify(const std::string& message, LPDISPATCH application_dispatch)
{
    // Status bar update requires COM automation on the UI thread.
    RJ2XCL_LOG_INFO("PostMessageBridge: notify — %s", message.c_str());
}

void PostMessageBridge::HandleSaveRequest(const std::string& viewer_id)
{
    RJ2XCL_LOG_INFO("PostMessageBridge: save-request from %s", viewer_id.c_str());

    // Open native Save dialog
    char file_path[MAX_PATH] = {};
    OPENFILENAMEA ofn = {};
    ofn.lStructSize = sizeof(OPENFILENAMEA);
    ofn.hwndOwner = NULL;
    ofn.lpstrFilter = "HTML File (*.html)\0*.html\0PNG Image (*.png)\0*.png\0PDF Document (*.pdf)\0*.pdf\0\0";
    ofn.lpstrFile = file_path;
    ofn.nMaxFile = MAX_PATH;
    ofn.lpstrTitle = "Guardar Contenido del Visor";
    ofn.Flags = OFN_OVERWRITEPROMPT | OFN_PATHMUSTEXIST;
    ofn.nFilterIndex = 1;

    if (!GetSaveFileNameA(&ofn)) {
        // User cancelled
        return;
    }

    std::string save_path(file_path);
    DWORD filter_index = ofn.nFilterIndex;

    // Ensure correct extension
    if (filter_index == 1 && save_path.find(".html") == std::string::npos) save_path += ".html";
    else if (filter_index == 2 && save_path.find(".png") == std::string::npos) save_path += ".png";
    else if (filter_index == 3 && save_path.find(".pdf") == std::string::npos) save_path += ".pdf";

    auto& vm = ViewerManager::Instance();

    if (filter_index == 1) {
        // HTML: Capture the actual DOM content via ExecuteScript (async)
        // This works even when the viewer was loaded from a file/URL
        std::string content = vm.CaptureViewerContent(viewer_id);
        if (!content.empty()) {
            // We have cached HTML (NavigateToString path) — write directly
            std::ofstream out(save_path, std::ios::binary);
            if (out.is_open()) {
                out.write(content.data(), content.size());
                out.close();
                RJ2XCL_LOG_INFO("PostMessageBridge: saved HTML to %s (%zu bytes)", save_path.c_str(), content.size());
            } else {
                RJ2XCL_LOG_WARN("PostMessageBridge: failed to write to %s", save_path.c_str());
            }
        } else {
            // No cached content (NavigateToFile/URL path) — capture DOM asynchronously
            vm.CaptureViewerPageSource(viewer_id, [save_path](const std::string& html) {
                if (html.empty()) {
                    RJ2XCL_LOG_WARN("PostMessageBridge: GetPageSource returned empty for save");
                    return;
                }
                std::ofstream out(save_path, std::ios::binary);
                if (out.is_open()) {
                    out.write(html.data(), html.size());
                    out.close();
                    RJ2XCL_LOG_INFO("PostMessageBridge: saved HTML (DOM capture) to %s (%zu bytes)", save_path.c_str(), html.size());
                } else {
                    RJ2XCL_LOG_WARN("PostMessageBridge: failed to write to %s", save_path.c_str());
                }
            });
        }
    } else if (filter_index == 2 || filter_index == 3) {
        // PNG or PDF: dispatch via WM_APP_SAVE_CONTENT (already on STA thread)
        // The STA message pump handles this in ViewerManager::RunSTAThread
        auto* req = new SaveContentRequest();
        req->viewer_id = viewer_id;
        req->file_path = save_path;
        req->format = (filter_index == 2) ? "png" : "pdf";

        // Post to ourselves (STA thread) — will be processed in the message pump
        PostThreadMessage(GetCurrentThreadId(), WM_APP_SAVE_CONTENT,
                          reinterpret_cast<WPARAM>(req), 0);
    }
}

} // namespace rj2xcl
