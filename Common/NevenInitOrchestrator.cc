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

#include "NevenInitOrchestrator.h"
#include "NevenProgressiveRegisterExport.h"
#include "LanguageManager.h"
#include "ConfigService.h"
#include "LogService.h"
#include <sstream>
#include <algorithm>

namespace neven {

InitOrchestrator& InitOrchestrator::Instance() {
    static InitOrchestrator instance;
    return instance;
}

InitOrchestrator::InitOrchestrator() = default;

void InitOrchestrator::ResetForTesting() {
    std::lock_guard<std::mutex> lock(state_mutex_);
    init_state_.store(InitState::NotStarted);
    cancellation_requested_.store(false);
    timing_data_.clear();
    engine_names_.clear();
    init_start_tick_ = 0;
    connector_.reset();
    ProgressiveRegistrar::Instance().ResetForTesting();
    StatusBarReporter::Instance().ResetForTesting();
}

void InitOrchestrator::FastInit(HANDLE job_handle, const std::string& functions_directory) {
    RJ2XCL_LOG_INFO("InitOrchestrator: FastInit starting");
    init_start_tick_ = GetTickCount();

    // ═══════════════════════════════════════════════════════════════════
    // Step 1: Read startup configuration
    // ═══════════════════════════════════════════════════════════════════
    auto& config_service = rj2xcl::ConfigService::Instance();
    auto full_config = config_service.GetConfig();
    config_ = parse_startup_config(full_config);

    // ═══════════════════════════════════════════════════════════════════
    // Step 2: Get configured engines and parse per-engine config
    // ═══════════════════════════════════════════════════════════════════
    auto& language_manager = rj2xcl::LanguageManager::Instance();
    const auto& services = language_manager.GetServices();

    engine_names_.clear();
    for (const auto& svc : services) {
        engine_names_.push_back(svc->name());
    }

    engine_configs_ = parse_engine_startup_configs(full_config, engine_names_);

    // Initialize timing data
    {
        std::lock_guard<std::mutex> lock(state_mutex_);
        timing_data_.resize(services.size());
        for (size_t i = 0; i < services.size(); i++) {
            timing_data_[i].engine_name = services[i]->name();
            timing_data_[i].final_status = HealthStatus::Pending;
        }
    }

    // ═══════════════════════════════════════════════════════════════════
    // Step 3: Set global init state
    // ═══════════════════════════════════════════════════════════════════
    init_state_.store(InitState::Connecting);
    cancellation_requested_.store(false);

    // ═══════════════════════════════════════════════════════════════════
    // Step 4: Report initial status
    // ═══════════════════════════════════════════════════════════════════
    if (config_.status_bar_updates) {
        StatusBarReporter::Instance().ReportProgress("NEVEN: Connecting language engines...");
    }

    // ═══════════════════════════════════════════════════════════════════
    // Step 5: Set up ProgressiveRegistrar
    // ═══════════════════════════════════════════════════════════════════
    int non_lazy_count = 0;
    for (const auto& ec : engine_configs_) {
        if (!ec.lazy_connect) non_lazy_count++;
    }
    ProgressiveRegistrar::Instance().SetExpectedEngineCount(non_lazy_count);

    // ═══════════════════════════════════════════════════════════════════
    // Step 6: Start watchdog timer
    // ═══════════════════════════════════════════════════════════════════
    watchdog_.Start(config_.total_timeout_ms, cancellation_requested_);

    // ═══════════════════════════════════════════════════════════════════
    // Step 7: Launch background connector threads
    // ═══════════════════════════════════════════════════════════════════
    connector_ = std::make_unique<BackgroundConnector>();

    // Launch engines in priority order (engine_configs_ is already sorted)
    for (const auto& ec : engine_configs_) {
        if (ec.lazy_connect) {
            RJ2XCL_LOG_INFO("InitOrchestrator: engine '%s' is lazy — deferring connection",
                            ec.name.c_str());
            continue;
        }

        // Find the service by name
        std::shared_ptr<LanguageService> service = nullptr;
        uint32_t engine_index = 0;
        for (uint32_t i = 0; i < services.size(); i++) {
            if (services[i]->name() == ec.name) {
                service = services[i];
                engine_index = i;
                break;
            }
        }

        if (!service) {
            RJ2XCL_LOG_WARN("InitOrchestrator: engine '%s' not found in services", ec.name.c_str());
            continue;
        }

        // Register task with watchdog (connection timeout as initial timeout)
        watchdog_.RegisterTask(engine_index, config_.connection_timeout_ms + config_.script_timeout_ms);

        // Launch worker thread
        connector_->ConnectEngine(
            engine_index,
            service,
            job_handle,
            cancellation_requested_,
            config_,
            &watchdog_,
            [this](uint32_t idx) { OnEngineReady(idx); },
            functions_directory);
    }

    // ═══════════════════════════════════════════════════════════════════
    // Step 8: Start registration timer (UI thread callback)
    // ═══════════════════════════════════════════════════════════════════
    start_registration_timer();

    DWORD elapsed = GetTickCount() - init_start_tick_;
    RJ2XCL_LOG_INFO("InitOrchestrator: FastInit completed in %lu ms, %d background threads launched",
                    elapsed, connector_->GetThreadCount());
}

void InitOrchestrator::OnEngineReady(uint32_t engine_index) {
    // Called from background worker thread when an engine completes (success or failure)
    HealthStatus status = connector_->GetEngineHealth(engine_index);
    EngineTimingData timing = connector_->GetTimingData(engine_index);

    // Update our timing data
    {
        std::lock_guard<std::mutex> lock(state_mutex_);
        if (engine_index < timing_data_.size()) {
            timing_data_[engine_index] = timing;
        }
    }

    // Enqueue for progressive registration
    ProgressiveRegistrar::Instance().EnqueueRegistration(engine_index);

    // Report status bar update
    if (config_.status_bar_updates) {
        std::string name = (engine_index < engine_names_.size()) ? engine_names_[engine_index] : "Unknown";
        if (status == HealthStatus::Ready || status == HealthStatus::Healthy) {
            StatusBarReporter::Instance().ReportEngineReady(name, timing.functions_registered);
        } else {
            StatusBarReporter::Instance().ReportProgress("NEVEN: " + name + " unavailable");
        }
    }

    // Check if all engines are done
    if (ProgressiveRegistrar::Instance().AllComplete()) {
        // Stop watchdog
        watchdog_.Stop();

        // Update global state
        init_state_.store(InitState::Ready);

        // Build and log startup report
        StartupReport report = GetStartupReport();

        if (report.total_elapsed_ms > 10000) {
            RJ2XCL_LOG_WARN("InitOrchestrator: startup took %lu ms (>10s)", report.total_elapsed_ms);
        }

        RJ2XCL_LOG_INFO("InitOrchestrator: startup complete — %d engines healthy, %d unavailable, "
                        "%d functions, %lu ms total",
                        report.engines_healthy, report.engines_unavailable,
                        report.total_functions_registered, report.total_elapsed_ms);

        // Report completion to status bar
        if (config_.status_bar_updates) {
            StatusBarReporter::Instance().ReportComplete(report);
        }
    }
}

void InitOrchestrator::CancelAndWait(DWORD timeout_ms) {
    RJ2XCL_LOG_INFO("InitOrchestrator: CancelAndWait called (timeout=%lu ms)", timeout_ms);

    // Signal cancellation
    cancellation_requested_.store(true);

    // Stop watchdog
    watchdog_.Stop();

    // Wait for background threads
    if (connector_) {
        bool completed = connector_->WaitAll(timeout_ms);
        if (!completed) {
            RJ2XCL_LOG_WARN("InitOrchestrator: background threads did not complete within %lu ms, detaching",
                            timeout_ms);
        }
    }

    init_state_.store(InitState::Failed);
    RJ2XCL_LOG_INFO("InitOrchestrator: CancelAndWait complete");
}

HealthStatus InitOrchestrator::GetEngineHealth(const std::string& engine_name) const {
    int idx = FindEngineIndex(engine_name);
    if (idx < 0) return HealthStatus::Pending;
    if (connector_) {
        return connector_->GetEngineHealth(static_cast<uint32_t>(idx));
    }
    return HealthStatus::Pending;
}

HealthStatus InitOrchestrator::GetEngineHealthByIndex(uint32_t engine_index) const {
    if (connector_) {
        return connector_->GetEngineHealth(engine_index);
    }
    return HealthStatus::Pending;
}

StartupReport InitOrchestrator::GetStartupReport() const {
    StartupReport report;
    report.total_elapsed_ms = GetTickCount() - init_start_tick_;

    std::lock_guard<std::mutex> lock(state_mutex_);
    report.engines = timing_data_;

    for (const auto& engine : timing_data_) {
        report.total_functions_registered += engine.functions_registered;
        report.total_files_loaded += engine.files_loaded;
        if (engine.final_status == HealthStatus::Ready ||
            engine.final_status == HealthStatus::Healthy ||
            engine.final_status == HealthStatus::Degraded) {
            report.engines_healthy++;
        } else if (engine.final_status == HealthStatus::Unavailable) {
            report.engines_unavailable++;
        }
    }

    return report;
}

bool InitOrchestrator::IsEngineReady(const std::string& engine_name) const {
    HealthStatus status = GetEngineHealth(engine_name);
    return status == HealthStatus::Ready;
}

std::string InitOrchestrator::GetEngineStatusMessage(const std::string& engine_name) const {
    HealthStatus status = GetEngineHealth(engine_name);

    switch (status) {
        case HealthStatus::Pending:
            return engine_name + ": pending initialization";
        case HealthStatus::Connecting:
            return engine_name + ": connecting (please wait)...";
        case HealthStatus::Healthy:
            return engine_name + ": connected, initializing...";
        case HealthStatus::LoadingFiles:
            return engine_name + ": loading user files...";
        case HealthStatus::Ready:
            return engine_name + ": ready";
        case HealthStatus::Degraded:
            return engine_name + ": ready (some files failed to load)";
        case HealthStatus::Unavailable:
            return engine_name + ": unavailable — check installation and restart Excel";
        default:
            return engine_name + ": unknown state";
    }
}

int InitOrchestrator::FindEngineIndex(const std::string& engine_name) const {
    for (size_t i = 0; i < engine_names_.size(); i++) {
        if (engine_names_[i] == engine_name) {
            return static_cast<int>(i);
        }
    }
    return -1;
}

} // namespace neven
