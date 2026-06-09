/**
 * Copyright (c) 2026 RJ2XCL Project — GPL v3
 *
 * @file PlutoManager.h
 * @brief Singleton managing the Pluto.jl server lifecycle for Advanced Mode.
 *
 * Pluto.jl runs as a SEPARATE Julia process (not inside ControlJulia.exe).
 * This manager handles launching, monitoring, and terminating the Pluto server,
 * as well as opening notebooks in the WebView2 viewer.
 */

#pragma once

#include <string>
#include <mutex>
#include <cstdint>
#include <windows.h>

namespace rj2xcl {

/**
 * @brief Singleton managing the Pluto.jl notebook server.
 *
 * Pluto.jl is launched as an independent Julia process serving notebooks
 * on localhost. The WebView2 viewer connects to it for Advanced Mode.
 */
class PlutoManager {
public:
    static PlutoManager& Instance();

    // ─── Lifecycle ───────────────────────────────────────────────────────

    /** @brief Read config, resolve Julia path. Called from RJ2XCL_Engine::Init(). */
    void Initialize();

    /** @brief Terminate Pluto if running. Called from xlAutoClose. */
    void Shutdown();

    // ─── Server Control ──────────────────────────────────────────────────

    /**
     * @brief Start the Pluto.jl server.
     * @return Status message: "Pluto started on port [port]" or error string.
     */
    std::string StartPluto();

    /**
     * @brief Stop the Pluto.jl server.
     * @return "Pluto stopped" or error string.
     */
    std::string StopPluto();

    /**
     * @brief Get current server status.
     * @return "running", "stopped", or "starting".
     */
    std::string GetStatus() const;

    // ─── Notebook Operations ─────────────────────────────────────────────

    /**
     * @brief Open a notebook in the Pluto server and display in WebView2.
     * @param notebook_path Absolute path to the .jl notebook file.
     * @return Viewer identifier string or error string.
     */
    std::string OpenNotebook(const std::string& notebook_path);

    // ─── Accessors ───────────────────────────────────────────────────────

    uint16_t GetConfiguredPort() const;
    bool IsRunning() const;
    bool WasStartedByThisSession() const;

private:
    PlutoManager();
    ~PlutoManager();
    PlutoManager(const PlutoManager&) = delete;
    PlutoManager& operator=(const PlutoManager&) = delete;

    /** @brief HTTP probe to check if a server is running on the port. */
    bool ProbePort(uint16_t port) const;

    /** @brief Wait for Pluto to become ready (HTTP probe polling). */
    bool WaitForReady(uint32_t timeout_ms = 30000);

    /** @brief Build the Julia command to launch Pluto. */
    std::string BuildPlutoCommand() const;

    enum class State { STOPPED, STARTING, RUNNING };
    State state_;

    HANDLE pluto_process_handle_;
    DWORD pluto_process_id_;
    uint16_t port_;
    std::string julia_path_;
    std::string pluto_viewer_id_;
    std::string pluto_secret_;
    bool started_by_this_session_;

    mutable std::mutex state_mutex_;
};

} // namespace rj2xcl
