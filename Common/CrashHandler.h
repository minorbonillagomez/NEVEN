/**
 * Copyright (c) 2026 RJ2XCL Project — GPL v3
 *
 * @file CrashHandler.h
 * @brief Local crash telemetry — captures unhandled exceptions and writes
 *        structured crash reports to C:\RJ2XCL\crashes\.
 *
 * No external dependencies. No data sent to servers. Privacy-first design.
 */

#pragma once

#include <windows.h>
#include <string>

namespace rj2xcl {

class CrashHandler {
public:
    /**
     * @brief Install the global SEH handler. Call once from xlAutoOpen.
     */
    static void Install();

    /**
     * @brief Uninstall the handler. Call from xlAutoClose.
     */
    static void Uninstall();

    /**
     * @brief Write a health snapshot to the telemetry log.
     * Called periodically (e.g., every 5 minutes) or on demand.
     */
    static void WriteHealthSnapshot();

    /**
     * @brief Record a soft error (non-fatal) for telemetry.
     * @param component Source component (e.g., "ViewerManager", "LanguageService")
     * @param message Error description
     */
    static void RecordSoftError(const char* component, const char* message);

private:
    static LONG WINAPI ExceptionFilter(EXCEPTION_POINTERS* pExceptionInfo);
    static void WriteCrashReport(EXCEPTION_POINTERS* pExceptionInfo);
    static std::string GetExceptionCodeName(DWORD code);
    static std::string CollectSystemInfo();
    static std::string CollectProcessMemoryInfo();
    static std::string GetLanguageServiceStatus();
    static std::string GetTimestamp();
    static std::string GetCrashDirectory();

    static LPTOP_LEVEL_EXCEPTION_FILTER previous_filter_;
    static int soft_error_count_;
};

} // namespace rj2xcl
