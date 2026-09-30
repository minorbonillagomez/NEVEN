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
 * NevenWatchdogTimer: Monitors total initialization time and terminates
 * stuck tasks. Runs on a dedicated thread, checking every 1 second.
 */

#pragma once

#include "NevenStartupTypes.h"
#include <atomic>
#include <mutex>
#include <unordered_map>
#include <Windows.h>

namespace neven {

/**
 * @brief Monitors initialization tasks and enforces timeouts.
 *
 * The watchdog runs on a dedicated thread, waking every 1 second to check:
 * 1. Whether the total initialization timeout has been exceeded.
 * 2. Whether any individual task has exceeded its per-task timeout without
 *    reporting progress.
 *
 * When a timeout is detected, the watchdog sets the cancellation token to
 * signal all background threads to stop.
 */
class WatchdogTimer {
public:
    WatchdogTimer();
    ~WatchdogTimer();

    /**
     * @brief Starts the watchdog on a dedicated thread.
     * @param total_timeout_ms Maximum total initialization time allowed.
     * @param cancellation_token Atomic flag to set when timeout occurs.
     */
    void Start(DWORD total_timeout_ms, std::atomic<bool>& cancellation_token);

    /** @brief Stops the watchdog thread (called when init completes normally). */
    void Stop();

    /**
     * @brief Registers a task for individual timeout monitoring.
     * @param engine_index Index of the engine/task to monitor.
     * @param timeout_ms Maximum time allowed for this task without progress.
     */
    void RegisterTask(uint32_t engine_index, DWORD timeout_ms);

    /**
     * @brief Marks a task as making progress (resets its individual timer).
     * @param engine_index Index of the engine/task reporting progress.
     */
    void ReportProgress(uint32_t engine_index);

    /**
     * @brief Marks a task as completed (no longer monitored).
     * @param engine_index Index of the completed engine/task.
     */
    void MarkCompleted(uint32_t engine_index);

    /** @brief Returns true if the watchdog thread is currently running. */
    bool IsRunning() const { return running_.load(); }

    /** @brief Returns true if a timeout was triggered. */
    bool TimedOut() const { return timed_out_.load(); }

private:
    /// Watchdog thread entry point.
    static unsigned __stdcall WatchdogThread(void* param);

    /// Internal check logic called every wake-up cycle.
    void CheckTimeouts();

    struct TaskInfo {
        DWORD timeout_ms = 0;
        DWORD last_progress_tick = 0;
        bool completed = false;
    };

    HANDLE thread_handle_ = nullptr;
    HANDLE stop_event_ = nullptr;
    std::atomic<bool>* cancellation_token_ = nullptr;
    DWORD total_timeout_ms_ = 60000;
    DWORD start_tick_ = 0;

    std::atomic<bool> running_{false};
    std::atomic<bool> timed_out_{false};

    std::unordered_map<uint32_t, TaskInfo> tasks_;
    std::mutex tasks_mutex_;
};

} // namespace neven
