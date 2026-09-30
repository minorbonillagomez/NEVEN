/**
 * @file sim_viewer.cc
 * @brief SimViewerManager implementation — WebView2 workspace for simulation UI.
 *
 * Phase 1: Uses NEVEN base's ViewerManager via xlUDF to create viewers.
 * Future: Direct WebView2 environment (own STA thread).
 *
 * Copyright (c) 2026 NEVEN Project — GPL v3
 */

#include "sim_viewer.h"
#include "sim_bridge.h"
#include "json11/json11.hpp"
#include <windows.h>
#include <fstream>
#include <sstream>

namespace neven_sim {

SimViewerManager& SimViewerManager::Instance() {
    static SimViewerManager instance;
    return instance;
}

SimViewerManager::SimViewerManager() {}

void SimViewerManager::Initialize() {
    // Phase 1: No own WebView2 environment needed.
    // We'll use NEVEN base's ViewerManager via =NEVEN.view() UDF
    // or create our own viewer once Phase 2 direct WebView2 is ready.
}

void SimViewerManager::Shutdown() {
    std::lock_guard<std::mutex> lock(mutex_);
    if (is_open_) {
        // Close viewer via NEVEN base
        CloseWorkspace();
    }
}

std::string SimViewerManager::OpenWorkspace() {
    std::lock_guard<std::mutex> lock(mutex_);

    // If already open, just report OK (single workspace window)
    if (is_open_) {
        return "OK (ya abierto)";
    }

    auto& bridge = SimBridge::Instance();
    if (!bridge.EnsureAvailable()) {
        return "NEVEN64.xll no disponible";
    }

    std::string home = bridge.GetHomePath();
    std::string workspace_path = home + "workspace\\sim-workspace.html";

    // Check if workspace HTML exists
    DWORD attrs = GetFileAttributesA(workspace_path.c_str());
    if (attrs == INVALID_FILE_ATTRIBUTES) {
        return "Workspace no encontrado: " + workspace_path;
    }

    // Convert to forward slashes for the viewer call
    std::string fwd_path;
    for (char c : workspace_path) {
        fwd_path += (c == '\\') ? '/' : c;
    }

    // Call NEVEN.v() via xlUDF — this opens the WebView2 viewer directly
    // Same mechanism as =NEVEN.v("path") from a cell
    XLOPER12 result;
    memset(&result, 0, sizeof(result));
    bridge.CallUDF_Public("NEVEN.v", fwd_path, result);

    is_open_ = true;
    viewer_id_ = "sim-workspace-1";

    return "OK";
}

void SimViewerManager::CloseWorkspace() {
    is_open_ = false;
    viewer_id_.clear();
}

bool SimViewerManager::IsOpen() const {
    return is_open_;
}

void SimViewerManager::SendFitResults(const std::string& assumption_name,
                                       const std::string& json_data) {
    if (!is_open_) return;
    std::string msg = "{\"type\":\"fit-results\",\"assumption\":\"" + assumption_name + "\",\"data\":" + json_data + "}";
    PostToWorkspace(msg);
}

void SimViewerManager::SendSimResults(const std::string& json_data) {
    if (!is_open_) return;
    std::string msg = "{\"type\":\"simulation-results\",\"data\":" + json_data + "}";
    PostToWorkspace(msg);
}

void SimViewerManager::SendSensitivity(const std::string& json_data) {
    if (!is_open_) return;
    std::string msg = "{\"type\":\"sensitivity\",\"data\":" + json_data + "}";
    PostToWorkspace(msg);
}

void SimViewerManager::SendStatus(const std::string& message) {
    if (!is_open_) return;
    std::string msg = "{\"type\":\"status\",\"message\":\"" + message + "\"}";
    PostToWorkspace(msg);
}

void SimViewerManager::SetMessageHandler(MessageHandler handler) {
    std::lock_guard<std::mutex> lock(mutex_);
    message_handler_ = handler;
}

void SimViewerManager::HandleWebMessage(const std::string& json_message) {
    // Parse incoming message from JS workspace
    std::string err;
    json11::Json json = json11::Json::parse(json_message, err);
    if (!err.empty() || !json.is_object()) {
        if (message_handler_) message_handler_("error", json_message);
        return;
    }

    std::string type = json["type"].string_value();

    if (type == "add-assumption") {
        // JS sends: { type: "add-assumption", name: "Ventas", range: "Sheet1!A1:A100" }
        if (message_handler_) message_handler_(type, json_message);
    }
    else if (type == "remove-assumption") {
        if (message_handler_) message_handler_(type, json_message);
    }
    else if (type == "run-simulation") {
        // JS sends: { type: "run-simulation", iterations: 1000000, model: "(v,c)->v-c" }
        if (message_handler_) message_handler_(type, json_message);
    }
    else if (type == "set-model") {
        if (message_handler_) message_handler_(type, json_message);
    }
    else if (type == "export-report") {
        if (message_handler_) message_handler_(type, json_message);
    }
    else {
        if (message_handler_) message_handler_(type, json_message);
    }
}

void SimViewerManager::PostToWorkspace(const std::string& json_message) {
    // Phase 1: Log/buffer messages. Phase 2: actual PostMessage to WebView2.
    // For now this is a placeholder — the WebView2 communication will be
    // implemented when we have our own viewer window with PostMessage bridge.
    (void)json_message;
}

} // namespace neven_sim
