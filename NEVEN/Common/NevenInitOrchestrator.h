/**
 * Copyright (c) 2026 NEVEN Project
 *
 * This file is part of NEVEN.
 *
 * NEVEN is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * NevenInitOrchestrator: Coordinates the entire startup sequence.
 * Owns the global initialization state and manages the transition from
 * synchronous to asynchronous phases.
 */

#pragma once

#include "NevenStartupTypes.h"
#include "NevenStartupConfig.h"
#include "NevenBackgroundConnector.h"
#include "NevenWatchdogTimer.h"
#include "NevenProgressiveRegistrar.h"
#include "NevenStatusBarReporter.h"
#include <atomic>
#include <mutex>
#include <vector>
#include <string>
#include <memory>
#include <Windows.h>

// Forward declarations
class LanguageService;
struct CallbackInfo;
class COMObjectMap;

namespace neven {

/**
 * @brief Coordinates the two-phase startup sequence.
 *
 * Phase 1 (UI thread, ≤3s): Read config, configure languages, create JobObject,
 * register placeholder functions, launch background threads.
 *
 * Phase 2 (background threads): Connect engines, run startup scripts, load user
 * files, enqueue progressive registration.
 *
 * Thread safety:
 * - init_state_ is std::atomic — lock-free reads from UI thread.
 * - timing_data_ protected by state_mutex_.
 * - cancellation_requested_ is std::atomic.
 */
class InitOrchestrator {
public:
    /** @brief Returns the singleton instance. */
    static InitOrchestrator& Instance();

    /**
     * @brief Phase 1: Fast synchronous init on UI thread (≤3s).
     *
     * Performs non-blocking operations: config reading, language configuration,
     * JobObject creation, placeholder registration, and background thread launch.
     *
     * @param job_handle Windows Job Object handle for child process management.
     * @param functions_directory Path to the user functions directory.
     */
    void FastInit(HANDLE job_handle, const std::string& functions_directory);

    /** @brief Returns the current global initialization state. */
    InitState GetInitState() const { return init_state_.load(); }

    /**
     * @brief Returns the health status of a specific engine.
     * @param engine_name Name of the engine (e.g., "R", "Julia").
     * @return HealthStatus for the engine, or Pending if not found.
     */
    HealthStatus GetEngineHealth(const std::string& engine_name) const;

    /**
     * @brief Returns the health status of a specific engine by index.
     * @param engine_index Index of the engine.
     * @return HealthStatus for the engine.
     */
    HealthStatus GetEngineHealthByIndex(uint32_t engine_index) const;

    /**
     * @brief Returns the startup report for NEVEN.STATUS().
     * @return Populated StartupReport with timing and status data.
     */
    StartupReport GetStartupReport() const;

    /**
     * @brief Signals all background threads to stop and waits for completion.
     * @param timeout_ms Maximum time to wait (default 5000ms).
     */
    void CancelAndWait(DWORD timeout_ms = 5000);

    /**
     * @brief Checks if a specific engine is ready for function calls.
     * @param engine_name Name of the engine.
     * @return true if the engine is in Ready state.
     */
    bool IsEngineReady(const std::string& engine_name) const;

    /**
     * @brief Returns a user-facing status message for an engine.
     * @param engine_name Name of the engine.
     * @return Descriptive message based on current health status.
     */
    std::string GetEngineStatusMessage(const std::string& engine_name) const;

    /**
     * @brief Returns the startup configuration.
     * @return Reference to the parsed startup config.
     */
    const StartupConfig& GetConfig() const { return config_; }

    /** @brief Resets internal state (for testing). */
    void ResetForTesting();

private:
    InitOrchestrator();
    ~InitOrchestrator() = default;
    InitOrchestrator(const InitOrchestrator&) = delete;
    InitOrchestrator& operator=(const InitOrchestrator&) = delete;

    /// Called by background workers when an engine completes.
    void OnEngineReady(uint32_t engine_index);

    /// Finds engine index by name. Returns -1 if not found.
    int FindEngineIndex(const std::string& engine_name) const;

    // State
    std::atomic<InitState> init_state_{InitState::NotStarted};
    std::atomic<bool> cancellation_requested_{false};
    mutable std::mutex state_mutex_;
    std::vector<EngineTimingData> timing_data_;
    std::vector<std::string> engine_names_;
    DWORD init_start_tick_ = 0;

    // Configuration
    StartupConfig config_;
    std::vector<EngineStartupConfig> engine_configs_;

    // Components
    std::unique_ptr<BackgroundConnector> connector_;
    WatchdogTimer watchdog_;
};

} // namespace neven
