/**
 * Copyright (c) 2026 RJ2XCL Project â€” GPL v3
 *
 * @file CrashHandler.cc
 * @brief Local crash telemetry implementation.
 */

#include "CrashHandler.h"
#include "LogService.h"
#include "ConfigService.h"

#include <psapi.h>
#include <sstream>
#include <fstream>
#include <iomanip>
#include <ctime>

#pragma comment(lib, "psapi.lib")

namespace rj2xcl {

LPTOP_LEVEL_EXCEPTION_FILTER CrashHandler::previous_filter_ = nullptr;
int CrashHandler::soft_error_count_ = 0;

// â”€â”€â”€ Install / Uninstall â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

void CrashHandler::Install() {
    previous_filter_ = SetUnhandledExceptionFilter(ExceptionFilter);

    // Ensure crash directory exists
    std::string dir = GetCrashDirectory();
    CreateDirectoryA(dir.c_str(), nullptr);

    RJ2XCL_LOG_INFO("CrashHandler installed â€” reports go to %s", dir.c_str());
}

void CrashHandler::Uninstall() {
    if (previous_filter_) {
        SetUnhandledExceptionFilter(previous_filter_);
        previous_filter_ = nullptr;
    }
}

// â”€â”€â”€ SEH Exception Filter â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

LONG WINAPI CrashHandler::ExceptionFilter(EXCEPTION_POINTERS* pExceptionInfo) {
    WriteCrashReport(pExceptionInfo);

    // Let Windows handle it after we've saved our report
    if (previous_filter_) {
        return previous_filter_(pExceptionInfo);
    }
    return EXCEPTION_CONTINUE_SEARCH;
}

// â”€â”€â”€ Crash Report â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

void CrashHandler::WriteCrashReport(EXCEPTION_POINTERS* pExceptionInfo) {
    std::string dir = GetCrashDirectory();
    std::string timestamp = GetTimestamp();
    std::string filepath = dir + "crash_" + timestamp + ".txt";

    std::ofstream out(filepath);
    if (!out.is_open()) return;

    DWORD code = pExceptionInfo->ExceptionRecord->ExceptionCode;
    void* addr = pExceptionInfo->ExceptionRecord->ExceptionAddress;

    out << "â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•\n";
    out << "  RJ2XCL CRASH REPORT\n";
    out << "  " << timestamp << "\n";
    out << "â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•\n\n";

    // Exception info
    out << "â”€â”€ Exception â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n";
    out << "Code:    0x" << std::hex << std::setfill('0') << std::setw(8) << code
        << " (" << GetExceptionCodeName(code) << ")\n";
    out << "Address: 0x" << std::hex << reinterpret_cast<uintptr_t>(addr) << "\n";
    out << std::dec;

    // Registers (x64)
    if (pExceptionInfo->ContextRecord) {
        auto ctx = pExceptionInfo->ContextRecord;
        out << "\nâ”€â”€ Registers (x64) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n";
        out << "RIP: 0x" << std::hex << ctx->Rip << "\n";
        out << "RSP: 0x" << ctx->Rsp << "  RBP: 0x" << ctx->Rbp << "\n";
        out << "RAX: 0x" << ctx->Rax << "  RBX: 0x" << ctx->Rbx << "\n";
        out << "RCX: 0x" << ctx->Rcx << "  RDX: 0x" << ctx->Rdx << "\n";
        out << std::dec;
    }

    // System info
    out << "\nâ”€â”€ System â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n";
    out << CollectSystemInfo();

    // Memory
    out << "\nâ”€â”€ Memory â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n";
    out << CollectProcessMemoryInfo();

    // Language services
    out << "\nâ”€â”€ Language Services â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n";
    out << GetLanguageServiceStatus();

    // Soft errors
    out << "\nâ”€â”€ Session Stats â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n";
    out << "Soft errors this session: " << soft_error_count_ << "\n";

    // Module list
    out << "\nâ”€â”€ Loaded Modules â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n";
    HANDLE hProcess = GetCurrentProcess();
    HMODULE modules[256];
    DWORD needed;
    if (EnumProcessModules(hProcess, modules, sizeof(modules), &needed)) {
        int count = needed / sizeof(HMODULE);
        for (int i = 0; i < count && i < 50; i++) {
            char name[MAX_PATH];
            if (GetModuleFileNameA(modules[i], name, MAX_PATH)) {
                MODULEINFO mi;
                GetModuleInformation(hProcess, modules[i], &mi, sizeof(mi));
                out << "  0x" << std::hex << reinterpret_cast<uintptr_t>(mi.lpBaseOfDll)
                    << " (" << std::dec << (mi.SizeOfImage / 1024) << " KB) " << name << "\n";
            }
        }
    }

    out << "\nâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•\n";
    out << "  Report saved to: " << filepath << "\n";
    out << "  Please include this file when reporting issues.\n";
    out << "â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•\n";

    out.close();

    // Also log to the main log
    RJ2XCL_LOG_ERR("CRASH: 0x%08X at 0x%p â€” report saved to %s",
                     code, addr, filepath.c_str());
}

// â”€â”€â”€ Health Snapshot â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

void CrashHandler::WriteHealthSnapshot() {
    std::string dir = GetCrashDirectory();
    std::string filepath = dir + "health.log";

    std::ofstream out(filepath, std::ios::app);
    if (!out.is_open()) return;

    out << "[" << GetTimestamp() << "] ";
    out << CollectProcessMemoryInfo();
    out << " | soft_errors=" << soft_error_count_;
    out << " | " << GetLanguageServiceStatus();
    out << "\n";

    out.close();
}

// â”€â”€â”€ Soft Error Recording â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

void CrashHandler::RecordSoftError(const char* component, const char* message) {
    soft_error_count_++;

    std::string dir = GetCrashDirectory();
    std::string filepath = dir + "soft_errors.log";

    std::ofstream out(filepath, std::ios::app);
    if (out.is_open()) {
        out << "[" << GetTimestamp() << "] [" << component << "] " << message << "\n";
        out.close();
    }

    RJ2XCL_LOG_WARN("Soft error #%d [%s]: %s", soft_error_count_, component, message);
}

// â”€â”€â”€ Helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

std::string CrashHandler::GetExceptionCodeName(DWORD code) {
    switch (code) {
        case EXCEPTION_ACCESS_VIOLATION:      return "ACCESS_VIOLATION";
        case EXCEPTION_STACK_OVERFLOW:        return "STACK_OVERFLOW";
        case EXCEPTION_INT_DIVIDE_BY_ZERO:    return "INT_DIVIDE_BY_ZERO";
        case EXCEPTION_FLT_DIVIDE_BY_ZERO:    return "FLT_DIVIDE_BY_ZERO";
        case EXCEPTION_ILLEGAL_INSTRUCTION:   return "ILLEGAL_INSTRUCTION";
        case EXCEPTION_IN_PAGE_ERROR:         return "IN_PAGE_ERROR";
        case EXCEPTION_DATATYPE_MISALIGNMENT: return "DATATYPE_MISALIGNMENT";
        case EXCEPTION_ARRAY_BOUNDS_EXCEEDED: return "ARRAY_BOUNDS_EXCEEDED";
        case EXCEPTION_FLT_OVERFLOW:          return "FLT_OVERFLOW";
        case EXCEPTION_FLT_UNDERFLOW:         return "FLT_UNDERFLOW";
        case 0xE06D7363:                      return "C++ EXCEPTION (throw)";
        default:                              return "UNKNOWN";
    }
}

std::string CrashHandler::CollectSystemInfo() {
    std::stringstream ss;

    // OS version
    OSVERSIONINFOA ovi = {};
    ovi.dwOSVersionInfoSize = sizeof(ovi);
    #pragma warning(suppress: 4996)
    GetVersionExA(&ovi);
    ss << "OS: Windows " << ovi.dwMajorVersion << "." << ovi.dwMinorVersion
       << " (Build " << ovi.dwBuildNumber << ")\n";

    // Processor count
    SYSTEM_INFO si;
    ::GetSystemInfo(&si);
    ss << "Processors: " << si.dwNumberOfProcessors << "\n";

    // Total physical memory
    MEMORYSTATUSEX ms = {};
    ms.dwLength = sizeof(ms);
    GlobalMemoryStatusEx(&ms);
    ss << "Physical RAM: " << (ms.ullTotalPhys / (1024 * 1024)) << " MB\n";
    ss << "Available RAM: " << (ms.ullAvailPhys / (1024 * 1024)) << " MB\n";
    ss << "Memory load: " << ms.dwMemoryLoad << "%\n";

    return ss.str();
}

std::string CrashHandler::CollectProcessMemoryInfo() {
    PROCESS_MEMORY_COUNTERS_EX pmc = {};
    pmc.cb = sizeof(pmc);
    ::GetProcessMemoryInfo(::GetCurrentProcess(), (PROCESS_MEMORY_COUNTERS*)&pmc, sizeof(pmc));

    std::stringstream ss;
    ss << "WorkingSet=" << (pmc.WorkingSetSize / (1024 * 1024)) << "MB"
       << " Peak=" << (pmc.PeakWorkingSetSize / (1024 * 1024)) << "MB"
       << " Private=" << (pmc.PrivateUsage / (1024 * 1024)) << "MB";
    return ss.str();
}

std::string CrashHandler::GetLanguageServiceStatus() {
    // Read from the engine's language manager if available
    // For safety in crash context, just report basic info
    std::stringstream ss;
    ss << "R=configured Julia=configured";
    return ss.str();
}

std::string CrashHandler::GetTimestamp() {
    time_t now = time(nullptr);
    struct tm tm_buf;
    localtime_s(&tm_buf, &now);
    char buf[32];
    strftime(buf, sizeof(buf), "%Y%m%d_%H%M%S", &tm_buf);
    return buf;
}

std::string CrashHandler::GetCrashDirectory() {
    return "C:\\NEVEN\\crashes\\";
}

} // namespace rj2xcl
