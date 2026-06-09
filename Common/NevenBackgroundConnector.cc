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

#include "NevenBackgroundConnector.h"
#include "NevenWatchdogTimer.h"
#include "LogService.h"
#include <process.h>
#include <algorithm>

// Forward declare LanguageService methods we need
#include "language_service.h"

namespace neven {

BackgroundConnector::BackgroundConnector() = default;

BackgroundConnector::~BackgroundConnector() {
    // Close any remaining thread handles
    std::lock_guard<std::mutex> lock(mutex_);
    for (HANDLE h : thread_handles_) {
        if (h) CloseHandle(h);
    }
    thread_handles_.clear();

    // Clean up allocated atomic health statuses
    for (auto* p : health_statuses_) {
        delete p;
    }
    health_statuses_.clear();
}

void BackgroundConnector::ConnectEngine(uint32_t engine_index,
                                         std::shared_ptr<LanguageService> service,
                                         HANDLE job_handle,
                                         std::atomic<bool>& cancellation_token,
                                         const StartupConfig& config,
                                         WatchdogTimer* watchdog,
                                         EngineReadyCallback on_ready,
                                         const std::string& functions_directory) {
    auto context = std::make_unique<WorkerContext>();
    context->engine_index = engine_index;
    context->service = service;
    context->job_handle = job_handle;
    context->cancellation_token = &cancellation_token;
    context->config = config;
    context->watchdog = watchdog;
    context->on_ready = on_ready;
    context->functions_directory = functions_directory;
    context->connector = this;

    // Initialize timing data and health status for this engine
    {
        std::lock_guard<std::mutex> lock(results_mutex_);
        // Ensure vectors are large enough
        if (timing_data_.size() <= engine_index) {
            timing_data_.resize(engine_index + 1);
        }
        if (health_statuses_.size() <= engine_index) {
            health_statuses_.resize(engine_index + 1, nullptr);
        }
        timing_data_[engine_index].engine_name = service->name();
        timing_data_[engine_index].final_status = HealthStatus::Connecting;
        if (!health_statuses_[engine_index]) {
            health_statuses_[engine_index] = new std::atomic<HealthStatus>(HealthStatus::Connecting);
        } else {
            health_statuses_[engine_index]->store(HealthStatus::Connecting);
        }
    }

    // Launch worker thread via _beginthreadex
    WorkerContext* ctx_ptr = context.get();
    HANDLE thread = reinterpret_cast<HANDLE>(
        _beginthreadex(nullptr, 0, EngineWorker, ctx_ptr, 0, nullptr));

    if (thread) {
        std::lock_guard<std::mutex> lock(mutex_);
        thread_handles_.push_back(thread);
        contexts_.push_back(std::move(context));
        RJ2XCL_LOG_INFO("BackgroundConnector: launched worker for engine %u (%s)",
                        engine_index, service->name().c_str());
    } else {
        RJ2XCL_LOG_ERR("BackgroundConnector: failed to create thread for engine %u (%s)",
                       engine_index, service->name().c_str());
        // Mark as unavailable
        std::lock_guard<std::mutex> lock(results_mutex_);
        health_statuses_[engine_index]->store(HealthStatus::Unavailable);
        timing_data_[engine_index].final_status = HealthStatus::Unavailable;
    }
}

bool BackgroundConnector::WaitAll(DWORD timeout_ms) {
    std::vector<HANDLE> handles;
    {
        std::lock_guard<std::mutex> lock(mutex_);
        handles = thread_handles_;
    }

    if (handles.empty()) return true;

    DWORD result = WaitForMultipleObjects(
        static_cast<DWORD>(handles.size()),
        handles.data(),
        TRUE,  // Wait for all
        timeout_ms);

    return (result != WAIT_TIMEOUT && result != WAIT_FAILED);
}

HANDLE BackgroundConnector::GetThreadHandle(uint32_t engine_index) const {
    std::lock_guard<std::mutex> lock(mutex_);
    for (const auto& ctx : contexts_) {
        if (ctx->engine_index == engine_index) {
            size_t idx = &ctx - &contexts_[0];
            if (idx < thread_handles_.size()) {
                return thread_handles_[idx];
            }
        }
    }
    return nullptr;
}

EngineTimingData BackgroundConnector::GetTimingData(uint32_t engine_index) const {
    std::lock_guard<std::mutex> lock(results_mutex_);
    if (engine_index < timing_data_.size()) {
        return timing_data_[engine_index];
    }
    return EngineTimingData{};
}

HealthStatus BackgroundConnector::GetEngineHealth(uint32_t engine_index) const {
    std::lock_guard<std::mutex> lock(results_mutex_);
    if (engine_index < health_statuses_.size() && health_statuses_[engine_index]) {
        return health_statuses_[engine_index]->load();
    }
    return HealthStatus::Pending;
}

int BackgroundConnector::GetThreadCount() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return static_cast<int>(thread_handles_.size());
}

DWORD BackgroundConnector::CalculateBackoffDelay(int retry_index) {
    // Exponential backoff: 50ms initial, doubling up to 800ms cap
    DWORD delay = 50;
    for (int i = 0; i < retry_index; i++) {
        delay *= 2;
        if (delay >= 800) {
            delay = 800;
            break;
        }
    }
    return (delay > 800) ? 800 : delay;
}

bool BackgroundConnector::ConnectWithRetry(LanguageService* service,
                                            HANDLE job_handle,
                                            DWORD timeout_ms,
                                            std::atomic<bool>* cancellation_token,
                                            WatchdogTimer* watchdog,
                                            uint32_t engine_index,
                                            int& retry_count) {
    DWORD start_tick = GetTickCount();
    retry_count = 0;

    while (true) {
        // Check cancellation between retries
        if (cancellation_token && cancellation_token->load()) {
            RJ2XCL_LOG_INFO("BackgroundConnector: engine %u connection cancelled", engine_index);
            return false;
        }

        // Check total elapsed time
        DWORD elapsed = GetTickCount() - start_tick;
        if (elapsed >= timeout_ms) {
            RJ2XCL_LOG_WARN("BackgroundConnector: engine %u connection timeout after %lu ms (%d retries)",
                            engine_index, elapsed, retry_count);
            return false;
        }

        // Attempt connection (this calls LanguageService::Connect which does
        // StartChildProcess + pipe connection internally)
        service->Connect(job_handle);

        if (service->connected()) {
            RJ2XCL_LOG_INFO("BackgroundConnector: engine %u connected after %d retries (%lu ms)",
                            engine_index, retry_count, GetTickCount() - start_tick);
            return true;
        }

        // Check if child process exited prematurely
        DWORD exit_code = 0;
        if (service->ProcessExitCode(&exit_code) && exit_code != STILL_ACTIVE) {
            RJ2XCL_LOG_WARN("BackgroundConnector: engine %u child process exited (code %lu), aborting",
                            engine_index, exit_code);
            return false;
        }

        // Report progress to watchdog
        if (watchdog) {
            watchdog->ReportProgress(engine_index);
        }

        // Exponential backoff sleep (no lock held during Sleep)
        DWORD delay = CalculateBackoffDelay(retry_count);
        Sleep(delay);
        retry_count++;
    }
}

unsigned __stdcall BackgroundConnector::EngineWorker(void* param) {
    auto* ctx = reinterpret_cast<WorkerContext*>(param);
    auto* connector = ctx->connector;
    uint32_t engine_index = ctx->engine_index;
    auto service = ctx->service;

    RJ2XCL_LOG_INFO("BackgroundConnector: worker started for engine %u (%s)",
                    engine_index, service->name().c_str());

    DWORD worker_start = GetTickCount();

    // ═══════════════════════════════════════════════════════════════════
    // Phase 1: Pipe Connection with Exponential Backoff
    // ═══════════════════════════════════════════════════════════════════
    {
        std::lock_guard<std::mutex> lock(connector->results_mutex_);
        connector->timing_data_[engine_index].connect_start_ms = worker_start;
    }

    int retry_count = 0;
    bool connected = ConnectWithRetry(
        service.get(),
        ctx->job_handle,
        ctx->config.connection_timeout_ms,
        ctx->cancellation_token,
        ctx->watchdog,
        engine_index,
        retry_count);

    DWORD connect_end = GetTickCount();
    {
        std::lock_guard<std::mutex> lock(connector->results_mutex_);
        connector->timing_data_[engine_index].connect_end_ms = connect_end;
        connector->timing_data_[engine_index].retry_count = retry_count;
    }

    if (!connected) {
        // Connection failed — mark as Unavailable
        {
            std::lock_guard<std::mutex> lock(connector->results_mutex_);
            connector->health_statuses_[engine_index]->store(HealthStatus::Unavailable);
            connector->timing_data_[engine_index].final_status = HealthStatus::Unavailable;
        }
        if (ctx->watchdog) ctx->watchdog->MarkCompleted(engine_index);
        // Still call on_ready so the orchestrator can register stubs
        if (ctx->on_ready) ctx->on_ready(engine_index);
        return 0;
    }

    // Connection succeeded — update health to Healthy
    {
        std::lock_guard<std::mutex> lock(connector->results_mutex_);
        connector->health_statuses_[engine_index]->store(HealthStatus::Healthy);
    }

    // ═══════════════════════════════════════════════════════════════════
    // Phase 2: Startup Script Execution
    // ═══════════════════════════════════════════════════════════════════
    if (ctx->cancellation_token && ctx->cancellation_token->load()) {
        if (ctx->watchdog) ctx->watchdog->MarkCompleted(engine_index);
        if (ctx->on_ready) ctx->on_ready(engine_index);
        return 0;
    }

    DWORD init_start = GetTickCount();
    {
        std::lock_guard<std::mutex> lock(connector->results_mutex_);
        connector->timing_data_[engine_index].init_start_ms = init_start;
    }

    // Report progress before potentially long operation
    if (ctx->watchdog) ctx->watchdog->ReportProgress(engine_index);

    // Send startup script via existing LanguageService::Initialize()
    service->Initialize();

    DWORD init_end = GetTickCount();
    {
        std::lock_guard<std::mutex> lock(connector->results_mutex_);
        connector->timing_data_[engine_index].init_end_ms = init_end;
    }

    // Check if startup script caused a crash
    DWORD exit_code = 0;
    if (service->ProcessExitCode(&exit_code) && exit_code != STILL_ACTIVE) {
        RJ2XCL_LOG_WARN("BackgroundConnector: engine %u crashed during startup script (code %lu)",
                        engine_index, exit_code);
        std::lock_guard<std::mutex> lock(connector->results_mutex_);
        connector->health_statuses_[engine_index]->store(HealthStatus::Unavailable);
        connector->timing_data_[engine_index].final_status = HealthStatus::Unavailable;
        if (ctx->watchdog) ctx->watchdog->MarkCompleted(engine_index);
        if (ctx->on_ready) ctx->on_ready(engine_index);
        return 0;
    }

    // ═══════════════════════════════════════════════════════════════════
    // Phase 3: User Function File Loading
    // ═══════════════════════════════════════════════════════════════════
    if (ctx->cancellation_token && ctx->cancellation_token->load()) {
        if (ctx->watchdog) ctx->watchdog->MarkCompleted(engine_index);
        if (ctx->on_ready) ctx->on_ready(engine_index);
        return 0;
    }

    {
        std::lock_guard<std::mutex> lock(connector->results_mutex_);
        connector->health_statuses_[engine_index]->store(HealthStatus::LoadingFiles);
    }

    DWORD files_start = GetTickCount();
    {
        std::lock_guard<std::mutex> lock(connector->results_mutex_);
        connector->timing_data_[engine_index].files_start_ms = files_start;
    }

    int files_loaded = 0;

    if (!ctx->functions_directory.empty()) {
        // Set loading timeout for this engine
        service->SetLoadingTimeout(ctx->config.file_timeout_ms);

        // Find and load files for this engine
        WIN32_FIND_DATAA find_data;
        std::string search_pattern = ctx->functions_directory + "\\*.*";
        HANDLE hFind = FindFirstFileA(search_pattern.c_str(), &find_data);

        if (hFind != INVALID_HANDLE_VALUE) {
            do {
                // Check cancellation
                if (ctx->cancellation_token && ctx->cancellation_token->load()) {
                    break;
                }

                if (find_data.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) {
                    continue;
                }

                std::string file_path = ctx->functions_directory + "\\" + find_data.cFileName;

                if (!service->ValidFile(file_path)) {
                    continue;
                }

                // Report progress before loading each file
                if (ctx->watchdog) ctx->watchdog->ReportProgress(engine_index);

                RJ2XCL_LOG_INFO("BackgroundConnector: engine %u loading file: %s",
                                engine_index, find_data.cFileName);

                service->ReadSourceFile(file_path);
                files_loaded++;

                // Check if engine crashed during file loading
                DWORD file_exit_code = 0;
                if (service->ProcessExitCode(&file_exit_code) && file_exit_code != STILL_ACTIVE) {
                    RJ2XCL_LOG_WARN("BackgroundConnector: engine %u crashed during file loading (%s)",
                                    engine_index, find_data.cFileName);
                    std::lock_guard<std::mutex> lock(connector->results_mutex_);
                    connector->health_statuses_[engine_index]->store(HealthStatus::Unavailable);
                    connector->timing_data_[engine_index].final_status = HealthStatus::Unavailable;
                    connector->timing_data_[engine_index].files_loaded = files_loaded;
                    connector->timing_data_[engine_index].files_end_ms = GetTickCount();
                    FindClose(hFind);
                    if (ctx->watchdog) ctx->watchdog->MarkCompleted(engine_index);
                    if (ctx->on_ready) ctx->on_ready(engine_index);
                    return 0;
                }

            } while (FindNextFileA(hFind, &find_data));
            FindClose(hFind);
        }

        // Restore normal timeout
        service->SetLoadingTimeout(0);
    }

    DWORD files_end = GetTickCount();
    {
        std::lock_guard<std::mutex> lock(connector->results_mutex_);
        connector->timing_data_[engine_index].files_end_ms = files_end;
        connector->timing_data_[engine_index].files_loaded = files_loaded;
        connector->health_statuses_[engine_index]->store(HealthStatus::Ready);
        connector->timing_data_[engine_index].final_status = HealthStatus::Ready;
    }

    // ═══════════════════════════════════════════════════════════════════
    // Phase 4: Signal Ready — Enqueue Registration
    // ═══════════════════════════════════════════════════════════════════
    if (ctx->watchdog) ctx->watchdog->MarkCompleted(engine_index);

    RJ2XCL_LOG_INFO("BackgroundConnector: engine %u (%s) ready — %d files loaded in %lu ms",
                    engine_index, service->name().c_str(), files_loaded,
                    files_end - worker_start);

    // Notify orchestrator that this engine is ready for registration
    if (ctx->on_ready) {
        ctx->on_ready(engine_index);
    }

    return 0;
}

} // namespace neven
