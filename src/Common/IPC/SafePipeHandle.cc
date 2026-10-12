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
 * RJ2XCL is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with RJ2XCL.  If not, see <http://www.gnu.org/licenses/>.
 */

#include "SafePipeHandle.h"

#include <utility>

#include "../LogService.h"

namespace rj2xcl {
namespace ipc {

SafePipeHandle::SafePipeHandle(HANDLE h)
    : handle_(h) {
    InitializeCriticalSection(&cs_);
}

SafePipeHandle::~SafePipeHandle() {
    Close();
    DeleteCriticalSection(&cs_);
}

SafePipeHandle::SafePipeHandle(SafePipeHandle&& other) noexcept
    : handle_(INVALID_HANDLE_VALUE) {
    InitializeCriticalSection(&cs_);

    EnterCriticalSection(&other.cs_);
    handle_ = other.handle_;
    other.handle_ = INVALID_HANDLE_VALUE;
    LeaveCriticalSection(&other.cs_);
}

SafePipeHandle& SafePipeHandle::operator=(SafePipeHandle&& other) noexcept {
    if (this != &other) {
        Close();

        EnterCriticalSection(&other.cs_);
        EnterCriticalSection(&cs_);

        handle_ = other.handle_;
        other.handle_ = INVALID_HANDLE_VALUE;

        LeaveCriticalSection(&cs_);
        LeaveCriticalSection(&other.cs_);
    }
    return *this;
}

bool SafePipeHandle::AtomicRead(char* buffer, DWORD buffer_size,
                                DWORD* bytes_read, LPOVERLAPPED overlapped) {
    EnterCriticalSection(&cs_);

    if (handle_ == INVALID_HANDLE_VALUE) {
        LeaveCriticalSection(&cs_);
        RJ2XCL_LOG_ERR("[SafePipeHandle] AtomicRead failed: handle is invalid. Reconnection needed.");
        return false;
    }

    BOOL result = ReadFile(handle_, buffer, buffer_size, bytes_read, overlapped);

    LeaveCriticalSection(&cs_);

    // ReadFile returns FALSE for pending async I/O (ERROR_IO_PENDING) which is
    // still a successful initiation of the operation.
    if (!result) {
        DWORD err = GetLastError();
        if (err == ERROR_IO_PENDING) {
            return true;
        }
        return false;
    }
    return true;
}

bool SafePipeHandle::AtomicWrite(const char* data, DWORD data_size,
                                 DWORD* bytes_written, LPOVERLAPPED overlapped) {
    EnterCriticalSection(&cs_);

    if (handle_ == INVALID_HANDLE_VALUE) {
        LeaveCriticalSection(&cs_);
        RJ2XCL_LOG_ERR("[SafePipeHandle] AtomicWrite failed: handle is invalid. Reconnection needed.");
        return false;
    }

    BOOL result = WriteFile(handle_, data, data_size, bytes_written, overlapped);

    LeaveCriticalSection(&cs_);

    // WriteFile returns FALSE for pending async I/O (ERROR_IO_PENDING) which is
    // still a successful initiation of the operation.
    if (!result) {
        DWORD err = GetLastError();
        if (err == ERROR_IO_PENDING) {
            return true;
        }
        return false;
    }
    return true;
}

bool SafePipeHandle::IsValid() const {
    EnterCriticalSection(&cs_);
    bool valid = (handle_ != INVALID_HANDLE_VALUE);
    LeaveCriticalSection(&cs_);
    return valid;
}

void SafePipeHandle::Close() {
    EnterCriticalSection(&cs_);

    if (handle_ != INVALID_HANDLE_VALUE) {
        CloseHandle(handle_);
        handle_ = INVALID_HANDLE_VALUE;
    }

    LeaveCriticalSection(&cs_);
}

} // namespace ipc
} // namespace rj2xcl
