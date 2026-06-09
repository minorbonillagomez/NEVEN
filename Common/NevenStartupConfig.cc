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

#include "NevenStartupConfig.h"
#include "LogService.h"
#include <algorithm>

namespace neven {

namespace {

/// Validates a timeout value. Returns the default if invalid.
DWORD validate_timeout(int value, DWORD default_value, const char* field_name) {
    if (value <= 0) {
        if (value < 0) {
            RJ2XCL_LOG_WARN("Startup config: '%s' is negative (%d), using default %lu ms",
                            field_name, value, default_value);
        }
        return default_value;
    }
    // Cap at 5 minutes for any individual timeout
    if (static_cast<DWORD>(value) > 300000) {
        RJ2XCL_LOG_WARN("Startup config: '%s' is too large (%d), capping at 300000 ms",
                        field_name, value);
        return 300000;
    }
    return static_cast<DWORD>(value);
}

} // anonymous namespace

StartupConfig parse_startup_config(const json11::Json& config) {
    StartupConfig result;

    auto neven_section = config["NEVEN"];
    if (neven_section.is_null()) {
        RJ2XCL_LOG_INFO("Startup config: no NEVEN section found, using all defaults");
        return result;
    }

    auto startup_section = neven_section["startup"];
    if (startup_section.is_null()) {
        RJ2XCL_LOG_INFO("Startup config: no startup section found, using all defaults");
        return result;
    }

    // Parse connection timeout
    if (!startup_section["connectionTimeoutMs"].is_null()) {
        int val = startup_section["connectionTimeoutMs"].int_value();
        result.connection_timeout_ms = validate_timeout(val, 15000, "connectionTimeoutMs");
    }

    // Parse script timeout
    if (!startup_section["scriptTimeoutMs"].is_null()) {
        int val = startup_section["scriptTimeoutMs"].int_value();
        result.script_timeout_ms = validate_timeout(val, 30000, "scriptTimeoutMs");
    }

    // Parse file timeout
    if (!startup_section["fileTimeoutMs"].is_null()) {
        int val = startup_section["fileTimeoutMs"].int_value();
        result.file_timeout_ms = validate_timeout(val, 30000, "fileTimeoutMs");
    }

    // Parse total timeout
    if (!startup_section["totalTimeoutMs"].is_null()) {
        int val = startup_section["totalTimeoutMs"].int_value();
        if (val <= 0) {
            if (val < 0) {
                RJ2XCL_LOG_WARN("Startup config: 'totalTimeoutMs' is negative (%d), using default 60000 ms", val);
            }
            result.total_timeout_ms = 60000;
        } else if (static_cast<DWORD>(val) > 600000) {
            RJ2XCL_LOG_WARN("Startup config: 'totalTimeoutMs' is too large (%d), capping at 600000 ms", val);
            result.total_timeout_ms = 600000;
        } else {
            result.total_timeout_ms = static_cast<DWORD>(val);
        }
    }

    // Parse max parallel connections
    if (!startup_section["maxParallelConnections"].is_null()) {
        int val = startup_section["maxParallelConnections"].int_value();
        if (val <= 0) {
            RJ2XCL_LOG_WARN("Startup config: 'maxParallelConnections' is invalid (%d), using default 3", val);
            result.max_parallel_connections = 3;
        } else if (val > 10) {
            RJ2XCL_LOG_WARN("Startup config: 'maxParallelConnections' is too large (%d), capping at 10", val);
            result.max_parallel_connections = 10;
        } else {
            result.max_parallel_connections = val;
        }
    }

    // Parse status bar updates flag
    if (startup_section["statusBarUpdates"].is_bool()) {
        result.status_bar_updates = startup_section["statusBarUpdates"].bool_value();
    }

    return result;
}

std::vector<EngineStartupConfig> parse_engine_startup_configs(
    const json11::Json& config,
    const std::vector<std::string>& engine_names) {

    std::vector<EngineStartupConfig> results;
    auto neven_section = config["NEVEN"];

    for (const auto& name : engine_names) {
        EngineStartupConfig engine_config;
        engine_config.name = name;

        if (!neven_section.is_null()) {
            auto engine_section = neven_section[name];
            if (!engine_section.is_null()) {
                // Parse startup priority
                if (!engine_section["startupPriority"].is_null()) {
                    int val = engine_section["startupPriority"].int_value();
                    if (val < 0) {
                        RJ2XCL_LOG_WARN("Startup config: '%s.startupPriority' is negative (%d), using 0",
                                        name.c_str(), val);
                        engine_config.startup_priority = 0;
                    } else {
                        engine_config.startup_priority = val;
                    }
                }

                // Parse lazy connect flag
                if (engine_section["lazyConnect"].is_bool()) {
                    engine_config.lazy_connect = engine_section["lazyConnect"].bool_value();
                }
            }
        }

        results.push_back(engine_config);
    }

    // Sort by ascending priority (lowest number = highest priority = first to connect)
    std::sort(results.begin(), results.end(),
              [](const EngineStartupConfig& a, const EngineStartupConfig& b) {
                  return a.startup_priority < b.startup_priority;
              });

    return results;
}

} // namespace neven
