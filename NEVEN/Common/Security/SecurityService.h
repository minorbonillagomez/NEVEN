/**
 * Copyright (c) 2026 RJ2XCL Project
 * 
 * SecurityService: Verifies script integrity.
 */

#pragma once

#include <string>

namespace rj2xcl {

    class SecurityService {
    public:
        /** @brief Returns the singleton instance of SecurityService. */
        static SecurityService& Instance();

        /**
         * @brief Verifies the integrity of a script file against its stored hash.
         * @param script_path Absolute path to the script file.
         * @return true if valid (or no hash file exists), false if hash mismatch.
         */
        bool VerifyScriptIntegrity(const std::string& script_path);

        /**
         * @brief Calculates the SHA-256 hash of a file.
         * @param file_path Absolute path to the file to hash.
         * @return Hex-encoded SHA-256 hash string.
         */
        std::string CalculateSHA256(const std::string& file_path);

    private:
        SecurityService() = default;
        ~SecurityService() = default;
        SecurityService(const SecurityService&) = delete;
        SecurityService& operator=(const SecurityService&) = delete;
    };

} // namespace rj2xcl
