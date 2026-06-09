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
 * NevenStartupConfig: Parses startup configuration from neven-config.json.
 * Validates values and applies sensible defaults for missing or invalid entries.
 */

#pragma once

#include "NevenStartupTypes.h"
#include "json11/json11.hpp"
#include <vector>
#include <string>

namespace neven {

/**
 * @brief Parses the startup configuration section from neven-config.json.
 *
 * Reads timeouts, parallelism settings, and per-engine priority/lazyConnect
 * flags. Invalid or missing values are replaced with sensible defaults and
 * a warning is logged.
 *
 * @param config The full parsed neven-config.json object.
 * @return Populated StartupConfig with validated values.
 */
StartupConfig parse_startup_config(const json11::Json& config);

/**
 * @brief Parses per-engine startup configuration (priority, lazyConnect).
 *
 * Reads the per-language sections from the config and extracts startup
 * priority and lazy connection flags.
 *
 * @param config The full parsed neven-config.json object.
 * @param engine_names List of configured engine names (e.g., {"R", "Julia"}).
 * @return Vector of EngineStartupConfig sorted by ascending priority.
 */
std::vector<EngineStartupConfig> parse_engine_startup_configs(
    const json11::Json& config,
    const std::vector<std::string>& engine_names);

} // namespace neven
