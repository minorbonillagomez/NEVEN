/**
 * @file sim_viewer.h
 * @brief SimViewerManager — WebView2 workspace for the simulation UI.
 *
 * Creates and manages the interactive workspace window where users configure
 * assumptions, run simulations, and view results.
 *
 * Copyright (c) 2026 NEVEN Project — GPL v3
 */

#pragma once

#include <string>
#include <mutex>
#include <functional>

namespace neven_sim {

/**
 * @brief Singleton managing the NEVEN-SIM WebView2 workspace window.
 *
 * Uses the PostMessage bridge pattern (JS ↔ C++) for bidirectional communication.
 * All WebView2 operations run on a dedicated STA thread.
 */
class SimViewerManager {
public:
    static SimViewerManager& Instance();

    /** @brief Initialize the viewer subsystem. */
    void Initialize();

    /** @brief Shutdown and close the workspace window. */
    void Shutdown();

    /** @brief Open (or focus) the simulation workspace window. */
    std::string OpenWorkspace();

    /** @brief Close the workspace window. */
    void CloseWorkspace();

    /** @brief Check if the workspace window is open. */
    bool IsOpen() const;

    // ─── Data Push (C++ → JS) ────────────────────────────────────────────

    /** @brief Send fit results to the workspace for visualization. */
    void SendFitResults(const std::string& assumption_name, const std::string& json_data);

    /** @brief Send simulation results (histogram + stats) to the workspace. */
    void SendSimResults(const std::string& json_data);

    /** @brief Send sensitivity analysis data (Tornado chart). */
    void SendSensitivity(const std::string& json_data);

    /** @brief Update status bar text in the workspace. */
    void SendStatus(const std::string& message);

    // ─── Message Handling (JS → C++) ─────────────────────────────────────

    /** @brief Set callback for when the workspace sends a command. */
    using MessageHandler = std::function<void(const std::string& type, const std::string& json_payload)>;
    void SetMessageHandler(MessageHandler handler);

    /** @brief Process a message received from the JS workspace (public for testability). */
    void HandleWebMessage(const std::string& json_message);

private:
    SimViewerManager();
    ~SimViewerManager() = default;
    SimViewerManager(const SimViewerManager&) = delete;
    SimViewerManager& operator=(const SimViewerManager&) = delete;

    void PostToWorkspace(const std::string& json_message);

    bool is_open_ = false;
    std::string viewer_id_;
    MessageHandler message_handler_;
    mutable std::mutex mutex_;
};

} // namespace neven_sim
