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
 * NevenStatusBarReporter: Throttled status bar updates via Excel's xlcMessage.
 * Updates are rate-limited to at most once per second to avoid flickering.
 */

#pragma once

#include "NevenStartupTypes.h"
#include <string>
#include <mutex>
#include <Windows.h>

namespace neven {

/**
 * @brief Reports startup progress to Excel's status bar.
 *
 * Thread-safe singleton that throttles updates to at most 1 per second.
 * Uses Excel's xlcMessage API to display messages in the status bar.
 * After initialization completes, displays a summary and clears after 5 seconds.
 */
class StatusBarReporter {
public:
    /** @brief Returns the singleton instance. */
    static StatusBarReporter& Instance();

    /**
     * @brief Posts a progress message to the status bar (throttled to 1/second).
     * @param message The message to display.
     */
    void ReportProgress(const std::string& message);

    /**
     * @brief Reports that a specific engine is ready.
     * @param engine_name Name of the engine (e.g., "R", "Julia").
     * @param function_count Number of functions registered for this engine.
     */
    void ReportEngineReady(const std::string& engine_name, int function_count);

    /**
     * @brief Reports final startup summary and schedules status bar clear.
     * @param report The completed startup report.
     */
    void ReportComplete(const StartupReport& report);

    /** @brief Clears the status bar message. */
    void Clear();

    /** @brief Returns the tick count of the last actual update (for testing). */
    DWORD GetLastUpdateTick() const { return last_update_tick_; }

    /** @brief Returns the total number of actual status bar updates performed. */
    int GetUpdateCount() const { return update_count_; }

    /** @brief Resets internal state (for testing). */
    void ResetForTesting();

private:
    StatusBarReporter();
    ~StatusBarReporter() = default;
    StatusBarReporter(const StatusBarReporter&) = delete;
    StatusBarReporter& operator=(const StatusBarReporter&) = delete;

    /// Actually sends the message to Excel's status bar.
    void SendToStatusBar(const std::string& message);

    DWORD last_update_tick_ = 0;
    DWORD init_start_tick_ = 0;
    int update_count_ = 0;
    std::mutex mutex_;

    static constexpr DWORD MIN_UPDATE_INTERVAL_MS = 1000;
};

} // namespace neven
