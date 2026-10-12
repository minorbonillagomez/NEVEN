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

#include "NevenWatchdogTimer.h"
#include "LogService.h"
#include <process.h>

namespace neven {

WatchdogTimer::WatchdogTimer() {
    stop_event_ = CreateEvent(nullptr, TRUE, FALSE, nullptr);
}

WatchdogTimer::~WatchdogTimer() {
    Stop();
    if (stop_event_) {
        CloseHandle(stop_event_);
        stop_event_ = nullptr;
    }
}

void WatchdogTimer::Start(DWORD total_timeout_ms, std::atomic<bool>& cancellation_token) {
    if (running_.load()) {
        return; // Already running
    }

    total_timeout_ms_ = total_timeout_ms;
    cancellation_token_ = &cancellation_token;
    start_tick_ = GetTickCount();
    timed_out_.store(false);

    // Reset stop event
    ResetEvent(stop_event_);

    // Launch watchdog thread via _beginthreadex
    thread_handle_ = reinterpret_cast<HANDLE>(
        _beginthreadex(nullptr, 0, WatchdogThread, this, 0, nullptr));

    if (thread_handle_) {
        running_.store(true);
        RJ2XCL_LOG_INFO("Watchdog: started (total timeout: %lu ms)", total_timeout_ms);
    } else {
        RJ2XCL_LOG_ERR("Watchdog: failed to start thread");
    }
}

void WatchdogTimer::Stop() {
    if (!running_.load()) {
        return;
    }

    // Signal the watchdog thread to stop
    SetEvent(stop_event_);

    // Wait for the thread to exit (max 2 seconds)
    if (thread_handle_) {
        DWORD wait_result = WaitForSingleObject(thread_handle_, 2000);
        if (wait_result == WAIT_TIMEOUT) {
            RJ2XCL_LOG_WARN("Watchdog: thread did not exit within 2 seconds");
        }
        CloseHandle(thread_handle_);
        thread_handle_ = nullptr;
    }

    running_.store(false);
    RJ2XCL_LOG_INFO("Watchdog: stopped");
}

void WatchdogTimer::RegisterTask(uint32_t engine_index, DWORD timeout_ms) {
    std::lock_guard<std::mutex> lock(tasks_mutex_);
    TaskInfo info;
    info.timeout_ms = timeout_ms;
    info.last_progress_tick = GetTickCount();
    info.completed = false;
    tasks_[engine_index] = info;
}

void WatchdogTimer::ReportProgress(uint32_t engine_index) {
    std::lock_guard<std::mutex> lock(tasks_mutex_);
    auto it = tasks_.find(engine_index);
    if (it != tasks_.end() && !it->second.completed) {
        it->second.last_progress_tick = GetTickCount();
    }
}

void WatchdogTimer::MarkCompleted(uint32_t engine_index) {
    std::lock_guard<std::mutex> lock(tasks_mutex_);
    auto it = tasks_.find(engine_index);
    if (it != tasks_.end()) {
        it->second.completed = true;
    }
}

unsigned __stdcall WatchdogTimer::WatchdogThread(void* param) {
    auto* self = reinterpret_cast<WatchdogTimer*>(param);

    while (true) {
        // Wait for 1 second or until stop event is signaled
        DWORD wait_result = WaitForSingleObject(self->stop_event_, 1000);

        if (wait_result == WAIT_OBJECT_0) {
            // Stop event signaled — exit cleanly
            break;
        }

        // Check timeouts
        self->CheckTimeouts();

        // If cancellation was triggered (by us or externally), exit
        if (self->cancellation_token_ && self->cancellation_token_->load()) {
            break;
        }
    }

    return 0;
}

void WatchdogTimer::CheckTimeouts() {
    DWORD now = GetTickCount();

    // Check total timeout
    DWORD elapsed = now - start_tick_;
    if (elapsed >= total_timeout_ms_) {
        RJ2XCL_LOG_WARN("Watchdog: total initialization timeout reached (%lu ms)", elapsed);
        timed_out_.store(true);
        if (cancellation_token_) {
            cancellation_token_->store(true);
        }
        return;
    }

    // Check individual task timeouts
    std::lock_guard<std::mutex> lock(tasks_mutex_);
    for (auto& [engine_index, task] : tasks_) {
        if (task.completed) {
            continue;
        }

        DWORD task_elapsed = now - task.last_progress_tick;
        if (task_elapsed >= task.timeout_ms) {
            RJ2XCL_LOG_WARN("Watchdog: engine %u exceeded individual timeout (%lu ms without progress)",
                            engine_index, task_elapsed);
            timed_out_.store(true);
            if (cancellation_token_) {
                cancellation_token_->store(true);
            }
            return;
        }
    }
}

} // namespace neven
