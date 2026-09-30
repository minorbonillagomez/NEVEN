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
 * NevenStartupTypes: Shared enums and data structures for the startup
 * optimization feature. Used by InitOrchestrator, BackgroundConnector,
 * WatchdogTimer, ProgressiveRegistrar, and StatusBarReporter.
 */

#pragma once

#include <string>
#include <vector>
#include <cstdint>
#include <Windows.h>

namespace neven {

/// Discrete stages of the initialization sequence.
enum class StartupPhase {
    Configure,    ///< Reading config, creating JobObject
    Connect,      ///< Background pipe connection in progress
    Initialize,   ///< Startup scripts executing
    LoadFiles,    ///< User function files loading
    Register,     ///< Progressive xlfRegister calls
    Complete      ///< All engines finalized
};

/// Global initialization state flag queryable by other components.
enum class InitState {
    NotStarted,   ///< Init has not been called yet
    Connecting,   ///< Background initialization in progress
    Ready,        ///< All engines finalized (healthy or unavailable)
    Failed        ///< Critical failure during init
};

/// Per-engine health status tracking the lifecycle of a language engine.
enum class HealthStatus {
    Pending,       ///< Configured but not yet started
    Connecting,    ///< Background thread is attempting pipe connection
    Healthy,       ///< Pipe connected, startup script completed
    LoadingFiles,  ///< User function files being loaded
    Ready,         ///< Fully initialized, functions registered
    Degraded,      ///< Partially initialized (some files failed)
    Unavailable    ///< Failed to connect or process crashed
};

/// Timing and status data collected for a single engine during startup.
struct EngineTimingData {
    std::string engine_name;
    DWORD connect_start_ms = 0;
    DWORD connect_end_ms = 0;
    DWORD init_start_ms = 0;
    DWORD init_end_ms = 0;
    DWORD files_start_ms = 0;
    DWORD files_end_ms = 0;
    int retry_count = 0;
    int files_loaded = 0;
    int functions_registered = 0;
    HealthStatus final_status = HealthStatus::Pending;
};

/// Aggregated startup report exposed via NEVEN.STATUS().
struct StartupReport {
    DWORD total_elapsed_ms = 0;
    std::vector<EngineTimingData> engines;
    int total_functions_registered = 0;
    int total_files_loaded = 0;
    int engines_healthy = 0;
    int engines_unavailable = 0;
};

/// Startup configuration parsed from neven-config.json.
struct StartupConfig {
    DWORD connection_timeout_ms = 15000;
    DWORD script_timeout_ms = 30000;
    DWORD file_timeout_ms = 30000;
    DWORD total_timeout_ms = 60000;
    int max_parallel_connections = 3;
    bool status_bar_updates = true;
};

/// Per-engine startup configuration.
struct EngineStartupConfig {
    std::string name;
    int startup_priority = 0;
    bool lazy_connect = false;
};

} // namespace neven
