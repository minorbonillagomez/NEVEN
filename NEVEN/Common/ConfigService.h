/**
 * Copyright (c) 2026 NEVEN Project
 * 
 * ConfigService: Manages application configuration, home paths, and dev flags.
 * Part of Layer 2: Modular Core
 */

#pragma once

#include <string>
#include <Windows.h>
#include "json11/json11.hpp"
#include "result.h"
#include "windows_api_functions.h"

namespace rj2xcl {

    class ConfigService {
    public:
        /** @brief Returns the singleton instance of ConfigService. */
        static ConfigService& Instance();

        /**
         * @brief Initializes the service by resolving the home path and loading configuration.
         * @return Success, or a FileError if the config file cannot be read.
         */
        Result<void, APIFunctions::FileError> Initialize();

        /**
         * @brief Returns the resolved NEVEN home directory path.
         * @return Absolute path to the home directory.
         */
        std::string GetHomePath() const { return home_directory_; }

        /**
         * @brief Returns the main application configuration object.
         * @return Parsed JSON configuration from neven-config.json.
         */
        json11::Json GetConfig() const { return config_; }

        /**
         * @brief Returns the developer option flags read from the Windows Registry.
         * @return Bitmask of developer flags.
         */
        DWORD GetDevFlags() const { return dev_flags_; }

        /**
         * @brief Reads and parses a JSON configuration file from the home directory.
         * @param filename Name of the JSON file to read (relative to home directory).
         * @return Parsed JSON object, or a FileError if the file cannot be read.
         */
        Result<json11::Json, APIFunctions::FileError> ReadJsonFile(const std::string &filename);

        // --- Centralized configuration getters ---

        /**
         * @brief Returns the call timeout in milliseconds.
         *
         * Defaults to 600000 ms (10 min). Clamped to a maximum of 1800000 ms (30 min).
         * @return Timeout value in milliseconds.
         */
        DWORD GetCallTimeoutMs() const {
            int val = config_["NEVEN"]["callTimeoutMs"].int_value();
            if (val <= 0 || val > 1800000) return 600000;
            return (DWORD)val;
        }

        /**
         * @brief Returns the maximum retry attempts for pipe reconnection.
         *
         * Defaults to 2. Clamped to a maximum of 10.
         * @return Number of retry attempts.
         */
        int GetMaxRetries() const {
            int val = config_["NEVEN"]["maxRetries"].int_value();
            if (val <= 0 || val > 10) return 2;
            return val;
        }

        /**
         * @brief Returns whether the code execution sandbox is enabled.
         * @return true if sandbox is enabled (default), false if explicitly disabled.
         */
        bool IsSandboxEnabled() const {
            if (config_["NEVEN"]["sandboxEnabled"].is_bool())
                return config_["NEVEN"]["sandboxEnabled"].bool_value();
            return true;
        }

        /**
         * @brief Attempts to disable the sandbox with user confirmation.
         *
         * Shows an Excel dialog (MessageBox) requiring explicit confirmation.
         * Logs the event with timestamp and Windows username on success.
         * Keeps sandbox enabled if the user cancels.
         *
         * @return true if user confirmed and sandbox was disabled, false if cancelled.
         */
        bool RequestSandboxDisable();

        /**
         * @brief Returns the directory path for graphics output files.
         * @return Configured graphics directory, or the default %USERPROFILE%\Documents\NEVEN\graphics.
         */
        std::string GetGraphicsDirectory() const {
            std::string dir = config_["NEVEN"]["graphicsDirectory"].string_value();
            return dir.empty() ? "%USERPROFILE%\\Documents\\NEVEN\\graphics" : dir;
        }

        /**
         * @brief Returns the call timeout for a specific language.
         *
         * Reads `NEVEN.<language_name>.callTimeoutMs` from the config.
         * Returns the per-language value if in range [1000, 1800000]; clamps
         * out-of-range positive values to the nearest bound; falls back to
         * the global `GetCallTimeoutMs()` if absent or non-positive.
         *
         * @param language_name Language name (e.g., "Julia", "R", "Python").
         * @return Per-language timeout if configured, otherwise the global timeout.
         */
        DWORD GetLanguageCallTimeoutMs(const std::string& language_name) const {
            int val = config_["NEVEN"][language_name]["callTimeoutMs"].int_value();
            if (val >= 1000 && val <= 1800000) return (DWORD)val;
            if (val > 0) {
                // Out of range — clamp to nearest valid bound
                return (val < 1000) ? 1000 : 1800000;
            }
            return GetCallTimeoutMs(); // Fall back to global
        }

        // --- Quarto configuration getters ---

        /**
         * @brief Returns the full Quarto configuration section.
         * @return Parsed JSON object for the "Quarto" key.
         */
        json11::Json GetQuartoConfig() const {
            return config_["Quarto"];
        }

        /**
         * @brief Returns true if Quarto integration is enabled (default: true).
         * @return true if enabled, false if explicitly disabled.
         */
        bool IsQuartoEnabled() const {
            if (config_["Quarto"]["enabled"].is_bool())
                return config_["Quarto"]["enabled"].bool_value();
            return true;
        }

        /**
         * @brief Returns the configured Quarto CLI path (empty = auto-discover).
         * @return Configured path string, or empty for auto-discovery.
         */
        std::string GetQuartoPath() const {
            return config_["Quarto"]["path"].string_value();
        }

        /**
         * @brief Returns the Quarto output directory (with env vars unexpanded).
         * @return Configured output directory, or the default %USERPROFILE%\Documents\NEVEN\reports.
         */
        std::string GetQuartoOutputDirectory() const {
            std::string dir = config_["Quarto"]["outputDirectory"].string_value();
            return dir.empty() ? "%USERPROFILE%\\Documents\\NEVEN\\reports" : dir;
        }

        /**
         * @brief Returns the default output format (html, pdf, or docx).
         *
         * Falls back to "html" if the configured value is not one of the three valid formats.
         * @return Normalized default format string.
         */
        std::string GetQuartoDefaultFormat() const {
            std::string fmt = config_["Quarto"]["defaultFormat"].string_value();
            if (fmt != "html" && fmt != "pdf" && fmt != "docx") return "html";
            return fmt;
        }

        /**
         * @brief Returns true if auto-open is enabled (default: true).
         * @return true if rendered output should be opened automatically.
         */
        bool IsQuartoAutoOpen() const {
            if (config_["Quarto"]["autoOpen"].is_bool())
                return config_["Quarto"]["autoOpen"].bool_value();
            return true;
        }

        /**
         * @brief Returns the Quarto render timeout in milliseconds.
         *
         * Default: 300000 (5 min). Clamped to [5000, 1800000].
         * Non-positive values return the default.
         * @return Timeout value in milliseconds.
         */
        DWORD GetQuartoTimeoutMs() const {
            int val = config_["Quarto"]["timeoutMs"].int_value();
            if (val < 5000) return (val > 0) ? 5000 : 300000;
            if (val > 1800000) return 1800000;
            return (DWORD)val;
        }

        // --- WebView2 configuration getters ---

        /** @brief Returns true if WebView2 viewer is enabled (default: true). */
        bool IsWebView2Enabled() const {
            if (config_["WebView2"]["enabled"].is_bool())
                return config_["WebView2"]["enabled"].bool_value();
            return true;
        }

        /** @brief Max concurrent viewer windows (default: 8, range 1-16). */
        int GetMaxViewers() const {
            int val = config_["WebView2"]["maxViewers"].int_value();
            if (val <= 0) return 8;
            if (val < 1) return 1;
            if (val > 16) return 16;
            return val;
        }

        /** @brief Max memory for WebView2 processes in MB (default: 512, range 128-2048). */
        int GetMaxMemoryMB() const {
            int val = config_["WebView2"]["maxMemoryMB"].int_value();
            if (val <= 0) return 512;
            if (val < 128) return 128;
            if (val > 2048) return 2048;
            return val;
        }

        /** @brief WebView2 user data folder (default: %NEVEN_HOME%/webview2-data). */
        std::string GetWebView2UserDataFolder() const {
            std::string dir = config_["WebView2"]["userDataFolder"].string_value();
            return dir.empty() ? home_directory_ + "webview2-data" : dir;
        }

        /** @brief Default viewer width (default: 800, range 400-3840). */
        int GetDefaultViewerWidth() const {
            int val = config_["WebView2"]["defaultWidth"].int_value();
            if (val <= 0) return 800;
            if (val < 400) return 400;
            if (val > 3840) return 3840;
            return val;
        }

        /** @brief Default viewer height (default: 600, range 300-2160). */
        int GetDefaultViewerHeight() const {
            int val = config_["WebView2"]["defaultHeight"].int_value();
            if (val <= 0) return 600;
            if (val < 300) return 300;
            if (val > 2160) return 2160;
            return val;
        }

        /** @brief Returns true if DevTools are enabled for debugging (default: false). */
        bool IsDevToolsEnabled() const {
            if (config_["WebView2"]["security"]["devToolsEnabled"].is_bool())
                return config_["WebView2"]["security"]["devToolsEnabled"].bool_value();
            return false;
        }

        // --- Pluto.jl configuration getters ---

        /** @brief Pluto server port (default: 1234, range 1024-65535). */
        uint16_t GetPlutoPort() const {
            int val = config_["Pluto"]["port"].int_value();
            if (val <= 0) return 1234;
            if (val < 1024) return 1024;
            if (val > 65535) return 65535;
            return static_cast<uint16_t>(val);
        }

    private:
        ConfigService();
        ~ConfigService() = default;
        ConfigService(const ConfigService&) = delete;
        ConfigService& operator=(const ConfigService&) = delete;

        /** @brief Validates config values for security (path traversal, range checks). */
        void ValidateConfig();

        std::string home_directory_;
        json11::Json config_;
        DWORD dev_flags_;
    };

} // namespace rj2xcl
