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

#pragma once

#include <Windows.h>

namespace rj2xcl {
namespace ipc {

/**
 * @brief RAII wrapper for Windows HANDLE with atomic validity checking.
 *
 * Prevents TOCTOU races by combining validity check and operation
 * under a single critical section. Ensures handles are always closed
 * on destruction or error.
 *
 * This class is move-only; copying is explicitly deleted to enforce
 * unique ownership of the underlying OS handle.
 */
class SafePipeHandle {
public:
    /**
     * @brief Constructs a SafePipeHandle wrapping the given OS handle.
     *
     * Initializes the internal CRITICAL_SECTION used for atomic operations.
     *
     * @param h The Windows HANDLE to wrap. Defaults to INVALID_HANDLE_VALUE.
     */
    explicit SafePipeHandle(HANDLE h = INVALID_HANDLE_VALUE);

    /**
     * @brief Destructor. Closes the handle and deletes the CRITICAL_SECTION.
     */
    ~SafePipeHandle();

    /**
     * @brief Move constructor. Transfers ownership from another SafePipeHandle.
     *
     * The source handle is set to INVALID_HANDLE_VALUE after the move.
     *
     * @param other The SafePipeHandle to move from.
     */
    SafePipeHandle(SafePipeHandle&& other) noexcept;

    /**
     * @brief Move assignment operator. Transfers ownership from another SafePipeHandle.
     *
     * Closes the current handle before taking ownership of the source.
     *
     * @param other The SafePipeHandle to move from.
     * @return Reference to this object.
     */
    SafePipeHandle& operator=(SafePipeHandle&& other) noexcept;

    // Copy operations are deleted — unique ownership semantics.
    SafePipeHandle(const SafePipeHandle&) = delete;
    SafePipeHandle& operator=(const SafePipeHandle&) = delete;

    /**
     * @brief Atomically validates handle and performs a read operation.
     *
     * Acquires the critical section, checks handle validity, performs ReadFile,
     * all within the same critical section to prevent TOCTOU races.
     *
     * @param buffer Output buffer for read data.
     * @param buffer_size Size of the output buffer in bytes.
     * @param bytes_read Output: number of bytes actually read.
     * @param overlapped OVERLAPPED structure for async I/O (may be nullptr for sync).
     * @return true if the read operation was initiated successfully.
     */
    bool AtomicRead(char* buffer, DWORD buffer_size,
                    DWORD* bytes_read, LPOVERLAPPED overlapped);

    /**
     * @brief Atomically validates handle and performs a write operation.
     *
     * Acquires the critical section, checks handle validity, performs WriteFile,
     * all within the same critical section to prevent TOCTOU races.
     *
     * @param data Pointer to data to write.
     * @param data_size Number of bytes to write.
     * @param bytes_written Output: number of bytes actually written.
     * @param overlapped OVERLAPPED structure for async I/O (may be nullptr for sync).
     * @return true if the write operation was initiated successfully.
     */
    bool AtomicWrite(const char* data, DWORD data_size,
                     DWORD* bytes_written, LPOVERLAPPED overlapped);

    /**
     * @brief Returns true if the handle is valid (not INVALID_HANDLE_VALUE).
     * @return true if the handle can be used for I/O operations.
     */
    bool IsValid() const;

    /**
     * @brief Closes the handle and resets to INVALID_HANDLE_VALUE.
     *
     * Thread-safe: acquires the critical section before closing.
     */
    void Close();

    /**
     * @brief Gets the raw handle value.
     *
     * Use for WaitForMultipleObjects or other APIs that require a raw HANDLE.
     * Do NOT close the returned handle directly — use Close() instead.
     *
     * @return The underlying Windows HANDLE.
     */
    HANDLE Get() const { return handle_; }

private:
    HANDLE handle_;                 ///< The underlying Windows pipe handle.
    mutable CRITICAL_SECTION cs_;   ///< Critical section for atomic operations.
};

} // namespace ipc
} // namespace rj2xcl
