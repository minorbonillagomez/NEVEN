/**
 * Copyright (c) 2026 RJ2XCL Project — GPL v3
 *
 * @file DiagnosticRouter.h
 * @brief Routes diagnostic messages (stdout/stderr) from language processes
 *        to the WebView2 REPL console.
 *
 * Receives Console messages from RunCallbackThread (R, Julia) and
 * piggybacked diagnostic text from Python function responses. Delivers
 * them to the REPL console via REPLBridge on the STA thread timer.
 */

#pragma once

#include <string>
#include <deque>
#include <mutex>
#include <unordered_map>
#include <vector>
#include <cstdint>

#include "variable.pb.h"

namespace rj2xcl {

/**
 * @brief A single diagnostic message destined for the REPL console.
 */
struct DiagnosticMessage {
    std::string language;    ///< "R", "Julia", "Python"
    std::string type;        ///< "output" or "warning"
    std::string text;        ///< Message content (UTF-8)
    int64_t timestamp;       ///< Milliseconds since epoch
};

/**
 * @brief Singleton that routes diagnostic messages from language processes
 *        to the REPL console.
 *
 * Thread safety:
 *   - Route() and RoutePythonDiagnostics() are called from RunCallbackThread
 *     (one per language) or the pipe read thread.
 *   - DeliverPending() is called from the STA timer (50ms interval).
 *   - FlushBufferToConsole() is called when the console opens.
 *   - All public methods are thread-safe.
 */
class DiagnosticRouter {
public:
    static DiagnosticRouter& Instance();

    // ─── Routing ─────────────────────────────────────────────────────────

    /**
     * @brief Route a Console protobuf message from a callback thread.
     * Thread-safe. Called from RunCallbackThread when operation_case == kConsole.
     * @param language Source language name ("R", "Julia").
     * @param console_msg The Console protobuf message.
     */
    void Route(const std::string& language,
               const RJ2XCLBuffers::Console& console_msg);

    /**
     * @brief Route Python diagnostic messages extracted from a function response.
     * Called from the pipe read thread after receiving a Python response.
     * @param console_output Stdout text captured during execution.
     * @param console_error_output Stderr text captured during execution.
     */
    void RoutePythonDiagnostics(const std::string& console_output,
                                const std::string& console_error_output);

    // ─── Delivery ────────────────────────────────────────────────────────

    /**
     * @brief Drain queued messages and deliver to WebView2.
     * Called from STA timer callback (50ms interval).
     */
    void DeliverPending();

    /**
     * @brief Deliver buffered messages when console opens.
     * Called from REPLManager::ShowConsole() or viewer-ready callback.
     */
    void FlushBufferToConsole();

    // ─── Toggle ──────────────────────────────────────────────────────────

    /**
     * @brief Set/clear the diagnostics-enabled flag (UI toggle).
     * @param enabled Whether diagnostic display is enabled.
     */
    void SetEnabled(bool enabled);

    /**
     * @brief Check if diagnostic display is enabled.
     * @return true if enabled.
     */
    bool IsEnabled() const;

    // ─── Lifecycle ───────────────────────────────────────────────────────

    /**
     * @brief Shutdown and release resources.
     * Called from xlAutoClose.
     */
    void Shutdown();

private:
    DiagnosticRouter();
    ~DiagnosticRouter();
    DiagnosticRouter(const DiagnosticRouter&) = delete;
    DiagnosticRouter& operator=(const DiagnosticRouter&) = delete;

    // ─── Per-language output buffer for when console is closed ────────────

    struct LanguageBuffer {
        std::deque<DiagnosticMessage> messages;
        static constexpr size_t MAX_MESSAGES = 200;

        void Push(const DiagnosticMessage& msg) {
            if (messages.size() >= MAX_MESSAGES) messages.pop_front();
            messages.push_back(msg);
        }
        void Clear() { messages.clear(); }
    };

    // ─── Internal helpers ────────────────────────────────────────────────

    void EnqueueMessage(DiagnosticMessage&& msg);
    int64_t CurrentTimestamp() const;

    // ─── State ───────────────────────────────────────────────────────────

    /// Thread-safe queue for pending messages (from callback threads → STA)
    std::mutex queue_mutex_;
    std::deque<DiagnosticMessage> pending_queue_;

    /// Per-language output buffer (when console is closed)
    mutable std::mutex buffer_mutex_;
    std::unordered_map<std::string, LanguageBuffer> buffers_;

    /// Diagnostics enabled flag
    bool enabled_ = true;
};

} // namespace rj2xcl
