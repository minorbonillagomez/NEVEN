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
 * LogService: Thread-safe structured logging with file output and
 * severity filtering. Uses the Singleton pattern.
 */

#pragma once

#include <string>
#include <mutex>
#include <fstream>
#include <memory>

namespace rj2xcl {

    enum class LogLevel {
        DEBUG_LVL,
        INFO_LVL,
        WARNING_LVL,
        ERROR_LVL
    };

    /**
     * @brief Thread-safe structured logging service.
     *
     * Writes timestamped, severity-tagged messages to a log file and
     * optionally to stdout. Designed for use via convenience macros:
     * `RJ2XCL_LOG_INFO("msg")`, `RJ2XCL_LOG_ERR("msg")`, etc.
     */
    class LogService {
    public:
        /** @brief Returns the singleton instance. */
        static LogService& Instance();

        /**
         * @brief Initializes the logging system.
         * @param log_file_path Path to the log file. If empty, defaults to %%TEMP%%/rj2xcl.log.
         */
        void Initialize(const std::string& log_file_path = "");

        /**
         * @brief Logs a message with the given severity level.
         * @param level Severity level (DEBUG, INFO, WARNING, ERROR).
         * @param message The message string.
         */
        void Log(LogLevel level, const std::string& message);

        /**
         * @brief Logs a printf-style formatted message.
         * @param level Severity level.
         * @param fmt Printf-style format string.
         */
        void Log(LogLevel level, const char* fmt, ...);

    private:
        LogService() : initialized_(false), level_filter_(LogLevel::DEBUG_LVL) {}
        ~LogService();
        LogService(const LogService&) = delete;
        LogService& operator=(const LogService&) = delete;

        std::string LevelToString(LogLevel level);
        
        bool initialized_;
        LogLevel level_filter_;
        std::string log_file_path_;
        std::ofstream log_file_;
        std::mutex mutex_;
    };

} // namespace rj2xcl

// Convenience Macros
#define RJ2XCL_LOG_DEBUG(fmt, ...) rj2xcl::LogService::Instance().Log(rj2xcl::LogLevel::DEBUG_LVL, fmt, ##__VA_ARGS__)
#define RJ2XCL_LOG_INFO(fmt, ...)  rj2xcl::LogService::Instance().Log(rj2xcl::LogLevel::INFO_LVL,  fmt, ##__VA_ARGS__)
#define RJ2XCL_LOG_WARN(fmt, ...)  rj2xcl::LogService::Instance().Log(rj2xcl::LogLevel::WARNING_LVL, fmt, ##__VA_ARGS__)
#define RJ2XCL_LOG_ERR(fmt, ...)   rj2xcl::LogService::Instance().Log(rj2xcl::LogLevel::ERROR_LVL, fmt, ##__VA_ARGS__)
