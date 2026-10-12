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
 * NevenBackgroundConnector: Manages per-engine worker threads that perform
 * blocking operations (process launch, pipe connection, startup script,
 * file loading) without blocking the UI thread.
 */

#pragma once

#include "NevenStartupTypes.h"
#include <atomic>
#include <mutex>
#include <vector>
#include <memory>
#include <string>
#include <functional>
#include <Windows.h>

// Forward declarations to avoid pulling in heavy headers
class LanguageService;

namespace neven {

class WatchdogTimer;

/// Callback type for when an engine completes initialization.
using EngineReadyCallback = std::function<void(uint32_t engine_index)>;

/**
 * @brief Manages per-engine worker threads for background initialization.
 *
 * Each engine gets its own worker thread that performs:
 * 1. Pipe connection with exponential backoff retry
 * 2. Startup script execution
 * 3. User function file loading
 * 4. Enqueue registration request
 *
 * Thread safety:
 * - Each worker thread operates on its own LanguageService instance.
 * - Shared state (timing data, health status) is protected by atomics or mutexes.
 * - No locks are held during blocking I/O operations.
 */
class BackgroundConnector {
public:
    BackgroundConnector();
    ~BackgroundConnector();

    /**
     * @brief Launches a worker thread for a single engine.
     * @param engine_index Index of the engine in the services vector.
     * @param service Shared pointer to the LanguageService.
     * @param job_handle Windows Job Object handle for child process management.
     * @param cancellation_token Atomic flag checked between retries.
     * @param config Startup configuration (timeouts).
     * @param watchdog Pointer to the watchdog timer for progress reporting.
     * @param on_ready Callback invoked when engine completes initialization.
     * @param functions_directory Path to the user functions directory.
     */
    void ConnectEngine(uint32_t engine_index,
                       std::shared_ptr<LanguageService> service,
                       HANDLE job_handle,
                       std::atomic<bool>& cancellation_token,
                       const StartupConfig& config,
                       WatchdogTimer* watchdog,
                       EngineReadyCallback on_ready,
                       const std::string& functions_directory);

    /**
     * @brief Waits for all worker threads to complete (with timeout).
     * @param timeout_ms Maximum time to wait.
     * @return true if all threads completed, false if timeout.
     */
    bool WaitAll(DWORD timeout_ms);

    /**
     * @brief Gets the thread handle for a specific engine.
     * @param engine_index Index of the engine.
     * @return Thread handle, or nullptr if not found.
     */
    HANDLE GetThreadHandle(uint32_t engine_index) const;

    /**
     * @brief Gets the timing data collected for a specific engine.
     * @param engine_index Index of the engine.
     * @return Copy of the timing data.
     */
    EngineTimingData GetTimingData(uint32_t engine_index) const;

    /**
     * @brief Gets the final health status of a specific engine.
     * @param engine_index Index of the engine.
     * @return The engine's health status.
     */
    HealthStatus GetEngineHealth(uint32_t engine_index) const;

    /** @brief Returns the number of worker threads launched. */
    int GetThreadCount() const;

private:
    /// Worker thread entry point.
    static unsigned __stdcall EngineWorker(void* param);

    /// Performs pipe connection with exponential backoff.
    static bool ConnectWithRetry(LanguageService* service,
                                 HANDLE job_handle,
                                 DWORD timeout_ms,
                                 std::atomic<bool>* cancellation_token,
                                 WatchdogTimer* watchdog,
                                 uint32_t engine_index,
                                 int& retry_count);

    /// Calculates exponential backoff delay for a given retry.
    static DWORD CalculateBackoffDelay(int retry_index);

    struct WorkerContext {
        uint32_t engine_index = 0;
        std::shared_ptr<LanguageService> service;
        HANDLE job_handle = nullptr;
        std::atomic<bool>* cancellation_token = nullptr;
        StartupConfig config;
        WatchdogTimer* watchdog = nullptr;
        EngineReadyCallback on_ready;
        std::string functions_directory;
        BackgroundConnector* connector = nullptr;
    };

    std::vector<HANDLE> thread_handles_;
    std::vector<std::unique_ptr<WorkerContext>> contexts_;
    mutable std::mutex mutex_;

    // Per-engine results (indexed by engine_index)
    std::vector<EngineTimingData> timing_data_;
    std::vector<std::atomic<HealthStatus>*> health_statuses_;
    mutable std::mutex results_mutex_;
};

} // namespace neven
