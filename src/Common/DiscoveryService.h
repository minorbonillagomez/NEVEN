/**
 * Copyright (c) 2026 RJ2XCL Project
 *
 * This file is part of RJ2XCL.
 *
 * RJ2XCL is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * DiscoveryService: Proactive detection of R and Julia installations
 * by scanning the Windows Registry and well-known filesystem paths.
 */

#pragma once

#include <string>
#include <vector>
#include <map>

namespace rj2xcl {

    /**
     * @brief Represents a single detected language runtime installation.
     */
    struct LanguageInstallation {
        std::string name;       ///< Language name (e.g., "R", "Julia")
        std::string version;    ///< Detected version string (e.g., "4.4.0")
        std::string home_path;  ///< Absolute path to the installation root
        bool is_64bit;          ///< Whether the installation is 64-bit
        int priority;           ///< Sort priority (higher = preferred)
    };

    class DiscoveryService {
    public:
        /** @brief Returns the singleton instance of DiscoveryService. */
        static DiscoveryService& Instance();

        /**
         * @brief Finds all R installations by scanning the Windows Registry.
         * @return Vector of detected R installations, sorted by priority.
         */
        std::vector<LanguageInstallation> FindR();

        /**
         * @brief Finds Julia installations via environment variables and known filesystem paths.
         * @return Vector of detected Julia installations, sorted by priority.
         */
        std::vector<LanguageInstallation> FindJulia();

        /**
         * @brief Finds Python installations via registry, environment variables, and filesystem.
         * @return Vector of detected Python installations, sorted by priority.
         */
        std::vector<LanguageInstallation> FindPython();

        /**
         * @brief Selects the best available installation for a given language.
         * @param language_name Language to search for (e.g., "R", "Julia", "Python").
         * @param preferred_tag Optional version tag to prefer (e.g., "4.4.0").
         * @param override_home Optional explicit home path that overrides discovery.
         * @return The highest-priority matching installation.
         */
        LanguageInstallation GetBestVersion(const std::string& language_name, 
                                           const std::string& preferred_tag = "",
                                           const std::string& override_home = "");

    private:
        DiscoveryService() = default;
        ~DiscoveryService() = default;
        DiscoveryService(const DiscoveryService&) = delete;
        DiscoveryService& operator=(const DiscoveryService&) = delete;

        /**
         * @brief Sorts installations by priority and filters out duplicates.
         * @param installs Vector of installations to sort and filter (modified in place).
         * @return Filtered and sorted vector of installations.
         */
        std::vector<LanguageInstallation> SortAndFilter(std::vector<LanguageInstallation>& installs);
    };

} // namespace rj2xcl
