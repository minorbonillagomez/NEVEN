/**
 * Copyright (c) 2026 RJ2XCL Project — GPL v3
 *
 * @file DiagnosticRouter.cc
 * @brief Implementation of the diagnostic message router.
 */

#include "DiagnosticRouter.h"
#include "REPLBridge.h"
#include "REPLManager.h"
#include "LogService.h"

#include <chrono>
#include <sstream>

namespace rj2xcl {

// ─── Singleton ──────────────────────────────────────────────────────────

DiagnosticRouter& DiagnosticRouter::Instance() {
    static DiagnosticRouter instance;
    return instance;
}

DiagnosticRouter::DiagnosticRouter() = default;
DiagnosticRouter::~DiagnosticRouter() = default;

// ─── Routing ────────────────────────────────────────────────────────────

void DiagnosticRouter::Route(const std::string& language,
                             const RJ2XCLBuffers::Console& console_msg) {
    // Determine type and text from the Console oneof
    std::string type;
    std::string text;

    switch (console_msg.message_case()) {
    case RJ2XCLBuffers::Console::kText:
        type = "output";
        text = console_msg.text();
        break;
    case RJ2XCLBuffers::Console::kErr:
        type = "warning";
        text = console_msg.err();
        break;
    default:
        // Malformed or unsupported message type (prompt, graphics, etc.)
        // Discard non-diagnostic console messages silently
        if (console_msg.message_case() == RJ2XCLBuffers::Console::MESSAGE_NOT_SET) {
            RJ2XCL_LOG_WARN("DiagnosticRouter: discarding malformed Console message "
                            "(empty text and err) from %s", language.c_str());
        }
        return;
    }

    // Discard empty messages
    if (text.empty()) {
        RJ2XCL_LOG_WARN("DiagnosticRouter: discarding empty %s message from %s",
                         type.c_str(), language.c_str());
        return;
    }

    DiagnosticMessage msg;
    msg.language = language;
    msg.type = type;
    msg.text = std::move(text);
    msg.timestamp = CurrentTimestamp();

    EnqueueMessage(std::move(msg));
}

void DiagnosticRouter::RoutePythonDiagnostics(const std::string& console_output,
                                               const std::string& console_error_output) {
    int64_t ts = CurrentTimestamp();

    // Route stdout lines as "output"
    if (!console_output.empty()) {
        std::istringstream stream(console_output);
        std::string line;
        while (std::getline(stream, line)) {
            if (line.empty()) continue;
            DiagnosticMessage msg;
            msg.language = "Python";
            msg.type = "output";
            msg.text = std::move(line);
            msg.timestamp = ts;
            EnqueueMessage(std::move(msg));
        }
    }

    // Route stderr lines as "warning"
    if (!console_error_output.empty()) {
        std::istringstream stream(console_error_output);
        std::string line;
        while (std::getline(stream, line)) {
            if (line.empty()) continue;
            DiagnosticMessage msg;
            msg.language = "Python";
            msg.type = "warning";
            msg.text = std::move(line);
            msg.timestamp = ts;
            EnqueueMessage(std::move(msg));
        }
    }
}

// ─── Delivery ───────────────────────────────────────────────────────────

void DiagnosticRouter::DeliverPending() {
    // Quick check — avoid locking if nothing to do
    {
        std::lock_guard<std::mutex> lock(buffer_mutex_);
        bool has_messages = false;
        for (auto& [lang, buffer] : buffers_) {
            if (!buffer.messages.empty()) { has_messages = true; break; }
        }
        if (!has_messages) return;
    }

    // Check if REPL console is open
    std::string viewer_id = REPLManager::Instance().GetConsoleViewerId();
    if (viewer_id.empty() || !REPLManager::Instance().IsConsoleOpen()) return;

    // Collect messages to deliver
    std::vector<DiagnosticMessage> to_deliver;
    {
        std::lock_guard<std::mutex> lock(buffer_mutex_);
        for (auto& [lang, buffer] : buffers_) {
            for (auto& msg : buffer.messages) {
                to_deliver.push_back(msg);
            }
            buffer.Clear();
        }
    }

    if (to_deliver.empty()) return;

    // Sort by timestamp and deliver
    std::sort(to_deliver.begin(), to_deliver.end(),
              [](const DiagnosticMessage& a, const DiagnosticMessage& b) {
                  return a.timestamp < b.timestamp;
              });

    for (auto& msg : to_deliver) {
        REPLBridge::SendDiagnostic(viewer_id, msg.language, msg.type,
                                   msg.text, msg.timestamp);
    }
}

void DiagnosticRouter::FlushBufferToConsole() {
    std::string viewer_id = REPLManager::Instance().GetConsoleViewerId();
    if (viewer_id.empty()) return;

    // Collect all buffered messages across languages
    std::vector<DiagnosticMessage> all_messages;
    {
        std::lock_guard<std::mutex> lock(buffer_mutex_);
        for (auto& [lang, buffer] : buffers_) {
            for (auto& msg : buffer.messages) {
                all_messages.push_back(msg);
            }
            buffer.Clear();
        }
    }

    if (all_messages.empty()) return;

    // Sort by timestamp for chronological delivery
    std::sort(all_messages.begin(), all_messages.end(),
              [](const DiagnosticMessage& a, const DiagnosticMessage& b) {
                  return a.timestamp < b.timestamp;
              });

    // Send as batch
    REPLBridge::SendDiagnosticBatch(viewer_id, all_messages);
}

// ─── Toggle ─────────────────────────────────────────────────────────────

void DiagnosticRouter::SetEnabled(bool enabled) {
    enabled_ = enabled;
}

bool DiagnosticRouter::IsEnabled() const {
    return enabled_;
}

// ─── Lifecycle ──────────────────────────────────────────────────────────

void DiagnosticRouter::Shutdown() {
    {
        std::lock_guard<std::mutex> lock(queue_mutex_);
        pending_queue_.clear();
    }
    {
        std::lock_guard<std::mutex> lock(buffer_mutex_);
        buffers_.clear();
    }
}

// ─── Internal Helpers ───────────────────────────────────────────────────

void DiagnosticRouter::EnqueueMessage(DiagnosticMessage&& msg) {
    // Check if console is open — if so, deliver via SendToViewer (thread-safe)
    std::string viewer_id = REPLManager::Instance().GetConsoleViewerId();
    if (!viewer_id.empty() && REPLManager::Instance().IsConsoleOpen()) {
        // SendToViewer uses PostThreadMessage internally — safe from any thread
        REPLBridge::SendDiagnostic(viewer_id, msg.language, msg.type,
                                   msg.text, msg.timestamp);
    } else {
        // Buffer for later delivery when console opens
        std::lock_guard<std::mutex> lock(buffer_mutex_);
        buffers_[msg.language].Push(msg);
    }
}

int64_t DiagnosticRouter::CurrentTimestamp() const {
    auto now = std::chrono::system_clock::now();
    auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(
        now.time_since_epoch());
    return ms.count();
}

} // namespace rj2xcl
