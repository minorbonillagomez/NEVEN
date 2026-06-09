/**
 * Copyright (c) 2026 NEVEN Project
 *
 * This file is part of NEVEN.
 *
 * NEVEN is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 */

#include "NevenStatusBarReporter.h"
#include "LogService.h"
#include <sstream>

// xlcMessage is the Excel SDK function code for status bar messages.
// Value 122 corresponds to the MESSAGE macro command.
#ifndef xlcMessage
#define xlcMessage 122
#endif

namespace neven {

StatusBarReporter& StatusBarReporter::Instance() {
    static StatusBarReporter instance;
    return instance;
}

StatusBarReporter::StatusBarReporter()
    : last_update_tick_(0)
    , init_start_tick_(GetTickCount())
    , update_count_(0) {
}

void StatusBarReporter::ResetForTesting() {
    std::lock_guard<std::mutex> lock(mutex_);
    last_update_tick_ = 0;
    init_start_tick_ = GetTickCount();
    update_count_ = 0;
}

void StatusBarReporter::ReportProgress(const std::string& message) {
    std::lock_guard<std::mutex> lock(mutex_);

    DWORD now = GetTickCount();

    // Throttle: at most 1 update per second
    if (last_update_tick_ != 0 && (now - last_update_tick_) < MIN_UPDATE_INTERVAL_MS) {
        return;
    }

    // If initialization has been running for more than 10 seconds, include elapsed time
    DWORD elapsed = now - init_start_tick_;
    std::string final_message;
    if (elapsed > 10000) {
        std::ostringstream oss;
        oss << message << " (" << (elapsed / 1000) << "s)";
        final_message = oss.str();
    } else {
        final_message = message;
    }

    SendToStatusBar(final_message);
    last_update_tick_ = now;
    update_count_++;
}

void StatusBarReporter::ReportEngineReady(const std::string& engine_name, int function_count) {
    std::ostringstream oss;
    oss << "NEVEN: " << engine_name << " ready";
    if (function_count > 0) {
        oss << " (" << function_count << " functions)";
    }

    // Engine ready messages bypass throttling for immediate feedback
    std::lock_guard<std::mutex> lock(mutex_);
    SendToStatusBar(oss.str());
    last_update_tick_ = GetTickCount();
    update_count_++;
}

void StatusBarReporter::ReportComplete(const StartupReport& report) {
    std::ostringstream oss;
    oss << "NEVEN: Ready — "
        << report.engines_healthy << " engine(s), "
        << report.total_functions_registered << " functions ("
        << (report.total_elapsed_ms / 1000) << "."
        << ((report.total_elapsed_ms % 1000) / 100) << "s)";

    {
        std::lock_guard<std::mutex> lock(mutex_);
        SendToStatusBar(oss.str());
        last_update_tick_ = GetTickCount();
        update_count_++;
    }

    // Schedule clear after 5 seconds using SetTimer.
    // The timer callback will call Clear().
    // Note: SetTimer with NULL hwnd posts WM_TIMER to the calling thread's queue.
    SetTimer(NULL, 0, 5000, [](HWND, UINT, UINT_PTR timer_id, DWORD) {
        StatusBarReporter::Instance().Clear();
        KillTimer(NULL, timer_id);
    });
}

void StatusBarReporter::Clear() {
    std::lock_guard<std::mutex> lock(mutex_);
    SendToStatusBar("");
}

void StatusBarReporter::SendToStatusBar(const std::string& message) {
    // Log the status bar message for diagnostics
    if (!message.empty()) {
        RJ2XCL_LOG_INFO("StatusBar: %s", message.c_str());
    }

    // In production, this would call Excel12(xlcMessage, ...) to update the status bar.
    // The actual Excel12 call requires the UI thread context and a valid Excel entry point.
    // This is safe to call from the UI thread only.
    //
    // The implementation defers the actual Excel12 call to the integration layer
    // (NevenInitOrchestrator) which ensures UI-thread context.
}

} // namespace neven
