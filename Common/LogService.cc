/**
 * Copyright (c) 2026 RJ2XCL Project
 * 
 * LogService Implementation.
 */

#include "LogService.h"
#include <windows.h>
#include <cstdio>
#include <cstdarg>
#include <ctime>
#include <iomanip>
#include <sstream>

namespace rj2xcl {

    LogService& LogService::Instance() {
        static LogService instance;
        return instance;
    }

    LogService::~LogService() {
        std::lock_guard<std::mutex> lock(mutex_);
        if (log_file_.is_open()) {
            log_file_.close();
        }
    }

    void LogService::Initialize(const std::string& log_file_path) {
        std::lock_guard<std::mutex> lock(mutex_);
        if (initialized_) return;

        log_file_path_ = log_file_path;
        if (!log_file_path_.empty()) {
            log_file_.open(log_file_path_, std::ios::app);
        }

        initialized_ = true;
    }

    void LogService::Log(LogLevel level, const std::string& message) {
        if (level < level_filter_) return;

        std::lock_guard<std::mutex> lock(mutex_);
        
        auto now = std::time(nullptr);
        auto tm = *std::localtime(&now);
        
        std::stringstream ss;
        ss << "[" << std::put_time(&tm, "%Y-%m-%d %H:%M:%S") << "] "
           << "[" << LevelToString(level) << "] "
           << message << "\n";
        
        std::string formal_message = ss.str();

        // 1. Output to debugger
        OutputDebugStringA(formal_message.c_str());

        // 2. Output to file
        if (log_file_.is_open()) {
            log_file_ << formal_message;
            log_file_.flush();
        }
    }

    void LogService::Log(LogLevel level, const char* fmt, ...) {
        if (level < level_filter_) return;

        char buffer[2048];
        va_list args;
        va_start(args, fmt);
        vsnprintf(buffer, sizeof(buffer), fmt, args);
        va_end(args);

        Log(level, std::string(buffer));
    }

    std::string LogService::LevelToString(LogLevel level) {
        switch (level) {
            case LogLevel::DEBUG_LVL:   return "DEBUG";
            case LogLevel::INFO_LVL:    return "INFO";
            case LogLevel::WARNING_LVL: return "WARN";
            case LogLevel::ERROR_LVL:   return "ERROR";
            default:                    return "UNKNOWN";
        }
    }

} // namespace rj2xcl
