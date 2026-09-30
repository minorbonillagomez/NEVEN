/**
 * Copyright (c) 2026 RJ2XCL Project — GPL v3
 *
 * @file REPLBridge.cc
 * @brief Implementation of the REPL-specific PostMessage bridge.
 */

#include "REPLBridge.h"
#include "REPLManager.h"
#include "REPLLanguageAccessor.h"
#include "ViewerManager.h"
#include "DiagnosticRouter.h"
#include "LogService.h"
#include "SandboxVerifier.h"
#include "json11/json11.hpp"

#include <process.h>
#include <sstream>

namespace rj2xcl {

// ─── Message Handling ───────────────────────────────────────────────────

void REPLBridge::OnWebMessageReceived(
    const std::string& viewer_id,
    const std::string& json_message)
{
    // Parse JSON
    std::string err;
    json11::Json msg = json11::Json::parse(json_message, err);

    if (!err.empty()) {
        RJ2XCL_LOG_WARN("REPLBridge: invalid JSON from %s: %s",
                         viewer_id.c_str(), err.c_str());
        return;
    }

    std::string action = msg["action"].string_value();

    if (action == "repl-exec") {
        std::string language = msg["language"].string_value();
        std::string code = msg["code"].string_value();
        int request_id = static_cast<int>(msg["id"].int_value());

        if (language.empty() || code.empty()) {
            RJ2XCL_LOG_WARN("REPLBridge: repl-exec missing language or code");
            SendResult(viewer_id, request_id, "error",
                       "Missing language or code field", language);
            return;
        }

        // Validate language is registered
        auto* accessor = REPLLanguageAccessor::Get();
        if (!accessor) {
            RJ2XCL_LOG_ERR("REPLBridge: language accessor not registered");
            SendResult(viewer_id, request_id, "error",
                       "Internal error: language services not initialized", language);
            return;
        }

        if (!accessor->IsLanguageRegistered(language)) {
            std::string error_msg = "Unknown language: " + language;
            RJ2XCL_LOG_WARN("REPLBridge: %s", error_msg.c_str());
            SendResult(viewer_id, request_id, "error", error_msg, language);
            return;
        }

        // Check if language is connected
        if (!accessor->IsLanguageConnected(language)) {
            SendResult(viewer_id, request_id, "error",
                       "Language engine not connected", language);
            return;
        }

        // Sandbox verification — apply same checks as Excel cell execution
        std::string rejection_reason;
        if (!security::SandboxVerifier::GetInstance().ValidateFromAnySource(
                code, security::ExecutionSource::REPL, rejection_reason)) {
            RJ2XCL_LOG_WARN("REPLBridge: code blocked by sandbox: %s",
                            rejection_reason.c_str());
            SendResult(viewer_id, request_id, "error",
                       rejection_reason, language);
            return;
        }

        // Store in history and dispatch
        REPLManager::Instance().AddToHistory(language, code);
        DispatchExec(viewer_id, language, code, request_id);

    } else if (action == "repl-interrupt") {
        std::string language = msg["language"].string_value();
        if (!language.empty()) {
            HandleInterrupt(language);
        }

    } else if (action == "set-active-language") {
        std::string language = msg["language"].string_value();
        if (!language.empty()) {
            REPLManager::Instance().SetLastActiveLanguage(language);
            // Console is ready — flush any buffered diagnostic messages
            DiagnosticRouter::Instance().FlushBufferToConsole();
        }

    } else {
        RJ2XCL_LOG_WARN("REPLBridge: unrecognized action '%s' from %s",
                         action.c_str(), viewer_id.c_str());
    }
}

// ─── Language Status ────────────────────────────────────────────────────

void REPLBridge::SendLanguageStatus(
    const std::string& viewer_id,
    const std::string& language,
    bool connected)
{
    json11::Json msg = json11::Json::object {
        { "action", "repl-status" },
        { "language", language },
        { "connected", connected }
    };

    std::string json_str = msg.dump();
    if (!ViewerManager::Instance().SendToViewer(viewer_id, json_str)) {
        RJ2XCL_LOG_WARN("REPLBridge: failed to send status to viewer %s",
                         viewer_id.c_str());
    }
}

// ─── Execution Dispatch ─────────────────────────────────────────────────

void REPLBridge::DispatchExec(
    const std::string& viewer_id,
    const std::string& language,
    const std::string& code,
    int request_id)
{
    // Allocate request on heap — worker thread owns it
    auto* request = new REPLExecRequest{viewer_id, language, code, request_id};

    HANDLE thread = (HANDLE)_beginthreadex(
        nullptr, 0, ExecWorkerThread, request, 0, nullptr);

    if (!thread) {
        RJ2XCL_LOG_ERR("REPLBridge: failed to create worker thread");
        SendResult(viewer_id, request_id, "error",
                   "Internal error: thread creation failed", language);
        delete request;
        return;
    }

    // Detach — worker thread manages its own lifetime
    CloseHandle(thread);
}

unsigned __stdcall REPLBridge::ExecWorkerThread(void* param) {
    auto* request = static_cast<REPLExecRequest*>(param);

    auto* accessor = REPLLanguageAccessor::Get();
    std::string output;
    if (accessor) {
        output = accessor->ExecuteShellCommand(request->language, request->code);
    } else {
        output = "Internal error: language services not available";
    }

    // Detect content type
    std::string content_type = DetectContentType(output);

    // Determine status — if output starts with "Error" or contains error markers
    std::string status = "ok";
    if (output.find("Error") == 0 || output.find("ERROR") == 0 ||
        output.find("error:") != std::string::npos) {
        status = "error";
    }

    SendResult(request->viewer_id, request->request_id,
               status, output, request->language, content_type);

    delete request;
    return 0;
}

// ─── Result Delivery ────────────────────────────────────────────────────

void REPLBridge::SendResult(
    const std::string& viewer_id,
    int request_id,
    const std::string& status,
    const std::string& output,
    const std::string& language,
    const std::string& content_type)
{
    json11::Json msg = json11::Json::object {
        { "action", "repl-result" },
        { "id", request_id },
        { "status", status },
        { "output", output },
        { "language", language },
        { "contentType", content_type }
    };

    std::string json_str = msg.dump();
    if (!ViewerManager::Instance().SendToViewer(viewer_id, json_str)) {
        RJ2XCL_LOG_WARN("REPLBridge: failed to send result to viewer %s (may be closed)",
                         viewer_id.c_str());
    }
}

// ─── Interrupt ──────────────────────────────────────────────────────────

void REPLBridge::HandleInterrupt(const std::string& language) {
    // TODO: Signal cancellation to the language service
    // This requires cooperation from the child process (e.g., sending a signal)
    RJ2XCL_LOG_INFO("REPLBridge: interrupt requested for %s", language.c_str());
}

// ─── Content Type Detection ─────────────────────────────────────────────

std::string REPLBridge::DetectContentType(const std::string& output) {
    // Check for HTML content markers
    if (output.find("<html") != std::string::npos ||
        output.find("<HTML") != std::string::npos ||
        output.find("<div") != std::string::npos ||
        output.find("<table") != std::string::npos ||
        output.find("text/html") != std::string::npos) {
        return "html";
    }

    // Check for image content (base64-encoded PNG/SVG)
    if (output.find("data:image/png") != std::string::npos ||
        output.find("data:image/svg") != std::string::npos ||
        (output.size() > 8 && output[0] == '\x89' && output[1] == 'P' &&
         output[2] == 'N' && output[3] == 'G')) {
        return "image";
    }

    return "text";
}

// ─── Diagnostic Delivery ────────────────────────────────────────────────

void REPLBridge::SendDiagnostic(
    const std::string& viewer_id,
    const std::string& language,
    const std::string& type,
    const std::string& text,
    int64_t timestamp)
{
    json11::Json msg = json11::Json::object {
        { "action", "diagnostic" },
        { "language", language },
        { "type", type },
        { "text", text },
        { "timestamp", static_cast<double>(timestamp) }
    };

    std::string json_str = msg.dump();
    if (!ViewerManager::Instance().SendToViewer(viewer_id, json_str)) {
        RJ2XCL_LOG_WARN("REPLBridge: failed to send diagnostic to viewer %s",
                         viewer_id.c_str());
    }
}

void REPLBridge::SendDiagnosticBatch(
    const std::string& viewer_id,
    const std::vector<DiagnosticMessage>& messages)
{
    if (messages.empty()) return;

    json11::Json::array msg_array;
    msg_array.reserve(messages.size());

    for (const auto& m : messages) {
        msg_array.push_back(json11::Json::object {
            { "language", m.language },
            { "type", m.type },
            { "text", m.text },
            { "timestamp", static_cast<double>(m.timestamp) }
        });
    }

    json11::Json msg = json11::Json::object {
        { "action", "diagnostic-batch" },
        { "messages", msg_array }
    };

    std::string json_str = msg.dump();
    if (!ViewerManager::Instance().SendToViewer(viewer_id, json_str)) {
        RJ2XCL_LOG_WARN("REPLBridge: failed to send diagnostic batch to viewer %s",
                         viewer_id.c_str());
    }
}

} // namespace rj2xcl
