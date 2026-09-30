/**
 * Copyright (c) 2026 RJ2XCL Project
 *
 * QuartoService: Manages Quarto CLI discovery, configuration, and render execution.
 * Stateless per-call process spawning — no persistent child process.
 * Part of Layer 2: Modular Core
 */

#pragma once

#include <string>
#include <Windows.h>
#include "XLCALL.h"

namespace rj2xcl {

    class QuartoService {
    public:
        /** @brief Returns the singleton instance of QuartoService. */
        static QuartoService& Instance();

        /**
         * @brief Called once during Init(). Reads config, discovers CLI, creates output dir.
         */
        void Initialize();

        /**
         * @brief Returns true if Quarto CLI was found and integration is enabled.
         * @return true if Quarto is ready to render.
         */
        bool IsAvailable() const { return available_; }

        /**
         * @brief Returns true if integration is enabled in config.
         * @return true if Quarto.enabled is true (or absent).
         */
        bool IsEnabled() const { return enabled_; }

        /**
         * @brief Main render entry point. Called from RJ_Q export.
         *
         * Returns output file path on success, or "ERROR: ..." / "BLOCKED: ..." string.
         * @param file_path Path to the .qmd file.
         * @param format Output format (html, pdf, or docx). Empty = use default.
         * @param data_range Optional XLOPER12 data range (nullable).
         * @return Result string for the Excel cell.
         */
        std::string Render(const std::string& file_path,
                           const std::string& format,
                           LPXLOPER12 data_range);

        // --- Input validation (public for testability) ---

        /**
         * @brief Validates input string against path traversal and command injection.
         * @param input The string to validate.
         * @param error_msg Output: error message if validation fails.
         * @return true if input is safe, false if blocked.
         */
        bool ValidateInputSecurity(const std::string& input, std::string& error_msg);

        /**
         * @brief Validates that the file path has a .qmd extension (case-insensitive).
         * @param resolved_path The resolved file path.
         * @return true if extension is .qmd.
         */
        bool ValidateExtension(const std::string& resolved_path);

        /**
         * @brief Validates and normalizes the output format.
         * @param format The format string to validate.
         * @param error_msg Output: error message if validation fails.
         * @return true if format is valid (html, pdf, or docx).
         */
        bool ValidateFormat(const std::string& format, std::string& error_msg);

        /**
         * @brief Resolves a file path: absolute paths pass through, relative paths
         *        are joined with the output directory.
         * @param file_path The input file path.
         * @return Resolved absolute path.
         */
        std::string ResolveFilePath(const std::string& file_path);

        /**
         * @brief Constructs the expected output file path by replacing .qmd extension.
         * @param qmd_path Path to the .qmd file.
         * @param format Output format (html, pdf, or docx).
         * @return Expected output file path.
         */
        static std::string ConstructOutputPath(const std::string& qmd_path,
                                               const std::string& format);

        /**
         * @brief Returns the configured output directory (expanded).
         * @return Expanded output directory path.
         */
        std::string GetOutputDirectory() const { return output_directory_; }

    private:
        QuartoService();
        ~QuartoService() = default;
        QuartoService(const QuartoService&) = delete;
        QuartoService& operator=(const QuartoService&) = delete;

        // --- Discovery ---
        std::string DiscoverQuartoCLI();
        bool ValidateExecutable(const std::string& path);

        // --- Process management ---
        std::string SpawnRender(const std::string& resolved_path,
                                const std::string& format,
                                const std::string& csv_path);

        // --- Data export ---
        std::string SerializeToCSV(LPXLOPER12 data_range,
                                   const std::string& qmd_stem);

        // --- Output directory ---
        bool EnsureOutputDirectory(std::string& error_msg);

        // --- State ---
        bool initialized_ = false;
        bool enabled_ = true;
        bool available_ = false;
        std::string quarto_path_;
        std::string output_directory_;
        std::string default_format_;
        bool auto_open_ = true;
        DWORD timeout_ms_ = 300000;
    };

} // namespace rj2xcl
