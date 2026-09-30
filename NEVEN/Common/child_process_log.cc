/**
 * Copyright (c) 2026 RJ2XCL Project
 *
 * Implementation of the unified ChildProcessLog facility.
 * See child_process_log.h for interface documentation.
 */

#include "child_process_log.h"

#include <cstdio>
#include <cstdarg>
#include <cstring>
#include <io.h>
#include <fcntl.h>

#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#include <windows.h>

namespace rj2xcl {

// Static member definitions
FILE* ChildProcessLog::log_file_ = nullptr;
std::string ChildProcessLog::log_path_;

bool ChildProcessLog::Initialize(const std::string& process_name) {
    // Close any previously opened log file
    if (log_file_) {
        fflush(log_file_);
        fclose(log_file_);
        log_file_ = nullptr;
    }

    // Build path: %TEMP%\control{process_name}.log
    char temp_path[MAX_PATH];
    DWORD len = GetTempPathA(MAX_PATH, temp_path);
    if (len == 0 || len >= MAX_PATH) {
        // Fallback: cannot determine temp path — discard silently
        log_file_ = nullptr;
        return false;
    }

    log_path_ = std::string(temp_path) + "control" + process_name + ".log";

    // Open with shared read access so the log can be read while the process runs
    HANDLE hFile = CreateFileA(
        log_path_.c_str(),
        GENERIC_WRITE,
        FILE_SHARE_READ | FILE_SHARE_DELETE,  // allow others to read/delete
        NULL,
        CREATE_ALWAYS,
        FILE_ATTRIBUTE_NORMAL,
        NULL);
    
    if (hFile == INVALID_HANDLE_VALUE) {
        log_file_ = nullptr;
        return false;
    }

    // Convert Win32 HANDLE to C FILE* for fprintf/vfprintf usage
    int fd = _open_osfhandle((intptr_t)hFile, 0);
    if (fd == -1) {
        CloseHandle(hFile);
        log_file_ = nullptr;
        return false;
    }

    log_file_ = _fdopen(fd, "w");
    if (!log_file_) {
        _close(fd); // also closes hFile
        return false;
    }

    return true;
}

void ChildProcessLog::Shutdown() {
    if (log_file_) {
        fflush(log_file_);
        fclose(log_file_);
        log_file_ = nullptr;
    }
    log_path_.clear();
}

void ChildProcessLog::Info(const char* fmt, ...) {
    va_list args;
    va_start(args, fmt);
    WriteTagged("[INFO] ", fmt, args);
    va_end(args);
}

void ChildProcessLog::Warn(const char* fmt, ...) {
    va_list args;
    va_start(args, fmt);
    WriteTagged("[WARN] ", fmt, args);
    va_end(args);
}

void ChildProcessLog::Error(const char* fmt, ...) {
    va_list args;
    va_start(args, fmt);
    WriteTagged("[ERROR] ", fmt, args);
    va_end(args);
}

void ChildProcessLog::Debug(const char* fmt, ...) {
    va_list args;
    va_start(args, fmt);
    WriteTagged("[DEBUG] ", fmt, args);
    va_end(args);
}

FILE* ChildProcessLog::GetFile() {
    return log_file_;
}

void ChildProcessLog::WriteTagged(const char* tag, const char* fmt, va_list args) {
    if (!log_file_) {
        return;  // Silently discard if no log file
    }

    fprintf(log_file_, "%s", tag);
    vfprintf(log_file_, fmt, args);
    fprintf(log_file_, "\n");
    fflush(log_file_);
}

} // namespace rj2xcl
