/**
 * Copyright (c) 2026 RJ2XCL Project
 */

#pragma once

#include <string>
#include <vector>
#include <Windows.h>

namespace rj2xcl {

    /**
     * @brief Singleton service for environment variable management.
     *
     * Provides utilities for setting system metadata, expanding environment
     * strings, and modifying the process PATH variable.
     */
    class EnvService {
    public:
        /** @brief Returns the singleton instance of EnvService. */
        static EnvService& Instance();

        /**
         * @brief Sets RJ2XCL version and build info in environment variables.
         * @param version Wide-string version identifier (e.g., L"2.0.0").
         * @param build_date Build date string (e.g., "2026-01-15").
         */
        void SetSystemMetadata(const std::wstring& version, const std::string& build_date);

        /**
         * @brief Expands environment variable references in a path string.
         * @param input Path string potentially containing %VAR% references.
         * @return Expanded path with all environment variables resolved.
         */
        std::string ExpandEnvStrings(const std::string& input);

        /**
         * @brief Prepends a directory to the beginning of %PATH% for the current process.
         * @param directory Absolute path to prepend.
         */
        void PrependToPath(const std::string& directory);

    private:
        EnvService() = default;
        ~EnvService() = default;
        EnvService(const EnvService&) = delete;
        EnvService& operator=(const EnvService&) = delete;
    };

    /**
     * @brief Reads an environment variable with NEVEN_ > RJ2XCL_ > BERT_ priority.
     *
     * Checks for the variable in the following order:
     * 1. NEVEN_{base_name} — if set, returns its value
     * 2. RJ2XCL_{base_name} — if set, returns its value
     * 3. BERT_{base_name} — if set, returns its value
     * 4. Returns empty string if none are set
     *
     * @param base_name Variable name without prefix (e.g., "HOME").
     * @return Value from highest-priority prefix found, or empty string.
     */
    std::string GetNevenEnvVar(const std::string& base_name);

} // namespace rj2xcl
