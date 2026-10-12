/**
 * Copyright (c) 2026 RJ2XCL Project
 *
 * Unified logging facility for child processes (ControlR, ControlJulia, ControlPython).
 *
 * Replaces the previous child_log.h macros that relied on an extern FILE* g_logFile.
 * Log output goes to %TEMP%\control{process_name}.log by default.
 *
 * Usage:
 *   #include "child_process_log.h"
 *
 *   // At process startup:
 *   rj2xcl::ChildProcessLog::Initialize("controlr");
 *
 *   // Throughout the code (macro or direct call):
 *   CHILD_LOG("message %s %d", str, num);
 *   CHILD_LOG_ERR("error: %d", err);
 *   rj2xcl::ChildProcessLog::Warn("timeout after %d ms", ms);
 *
 *   // At process shutdown:
 *   rj2xcl::ChildProcessLog::Shutdown();
 */

#pragma once

#include <cstdio>
#include <cstdarg>
#include <string>

namespace rj2xcl {

/**
 * @brief Logging facility for child processes (ControlR/Julia/Python).
 *
 * Writes to %TEMP%\control{process_name}.log by default.
 * Replaces:
 *   - Hardcoded "C:\RJ2XCL\controlr.log" paths
 *   - Raw std::cout/std::cerr in ControlJulia
 *   - Inconsistent g_logFile management across processes
 */
class ChildProcessLog {
public:
    /**
     * @brief Opens the log file for a given process name.
     * @param process_name E.g., "controlr", "controljulia", "controlpython".
     * @return true if log file opened successfully.
     *
     * The log file is created at %TEMP%\control{process_name}.log.
     * If the file cannot be opened, subsequent log calls silently discard messages.
     */
    static bool Initialize(const std::string& process_name);

    /**
     * @brief Flushes and closes the log file.
     *
     * Safe to call even if Initialize() was never called or failed.
     */
    static void Shutdown();

    /** @brief Printf-style log at INFO level. Prefixes with [INFO]. */
    static void Info(const char* fmt, ...);

    /** @brief Printf-style log at WARNING level. Prefixes with [WARN]. */
    static void Warn(const char* fmt, ...);

    /** @brief Printf-style log at ERROR level. Prefixes with [ERROR]. */
    static void Error(const char* fmt, ...);

    /** @brief Printf-style log at DEBUG level. Prefixes with [DEBUG]. */
    static void Debug(const char* fmt, ...);

    /**
     * @brief Returns the raw FILE* for legacy compatibility.
     * @return The log file pointer, or nullptr if not initialized.
     */
    static FILE* GetFile();

private:
    /** @brief Internal helper that writes a tagged, formatted message. */
    static void WriteTagged(const char* tag, const char* fmt, va_list args);

    static FILE* log_file_;
    static std::string log_path_;
};

} // namespace rj2xcl

// ─── Backward-compatible macros ─────────────────────────────────────────────
// Same call-site syntax as the original child_log.h macros, now routed
// through the ChildProcessLog class instead of a raw extern FILE*.

#define CHILD_LOG(fmt, ...)       rj2xcl::ChildProcessLog::Info(fmt, ##__VA_ARGS__)
#define CHILD_LOG_WARN(fmt, ...)  rj2xcl::ChildProcessLog::Warn(fmt, ##__VA_ARGS__)
#define CHILD_LOG_ERR(fmt, ...)   rj2xcl::ChildProcessLog::Error(fmt, ##__VA_ARGS__)
#define CHILD_LOG_DEBUG(fmt, ...) rj2xcl::ChildProcessLog::Debug(fmt, ##__VA_ARGS__)
