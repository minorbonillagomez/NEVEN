/**
 * Copyright (c) 2026 RJ2XCL Project
 */

#pragma once

#include <Windows.h>
#include <utility>

namespace rj2xcl {

    /**
 * @brief RAII wrapper for Windows HANDLE.
 *
 * Ensures CloseHandle is called when the object goes out of scope.
 * Supports move semantics but prevents copying to enforce unique ownership.
 */
class UniqueHandle {
public:
    /**
     * @brief Constructs a UniqueHandle, optionally wrapping an existing HANDLE.
     * @param handle Raw Windows HANDLE to manage (default: INVALID_HANDLE_VALUE).
     */
    UniqueHandle(HANDLE handle = INVALID_HANDLE_VALUE) : handle_(handle) {}

    /** @brief Destructor. Closes the handle if valid. */
    ~UniqueHandle() {
        Close();
    }

    // Prevent copying
    UniqueHandle(const UniqueHandle&) = delete;
    UniqueHandle& operator=(const UniqueHandle&) = delete;

    /**
     * @brief Move constructor. Transfers ownership from another UniqueHandle.
     * @param other Source handle (left in released state).
     */
    UniqueHandle(UniqueHandle&& other) noexcept : handle_(other.release()) {}

    /**
     * @brief Move assignment. Closes current handle and takes ownership.
     * @param other Source handle (left in released state).
     * @return Reference to this.
     */
    UniqueHandle& operator=(UniqueHandle&& other) noexcept {
        if (this != &other) {
            reset(other.release());
        }
        return *this;
    }

    /**
     * @brief Closes the current handle and replaces it with a new one.
     * @param handle New handle to manage (default: INVALID_HANDLE_VALUE).
     */
    void reset(HANDLE handle = INVALID_HANDLE_VALUE) {
        Close();
        handle_ = handle;
    }

    /**
     * @brief Releases ownership without closing the handle.
     * @return The raw HANDLE (caller assumes ownership).
     */
    HANDLE release() noexcept {
        HANDLE temp = handle_;
        handle_ = INVALID_HANDLE_VALUE;
        return temp;
    }

    /**
     * @brief Returns the managed HANDLE without releasing ownership.
     * @return The raw HANDLE value.
     */
    HANDLE get() const noexcept {
        return handle_;
    }

    /**
     * @brief Checks whether the handle is valid (not null and not INVALID_HANDLE_VALUE).
     * @return true if the handle is valid.
     */
    bool is_valid() const noexcept {
        return handle_ != nullptr && handle_ != INVALID_HANDLE_VALUE;
    }

    /**
     * @brief Implicit conversion to HANDLE for use with Windows APIs.
     * @return The raw HANDLE value.
     */
    operator HANDLE() const noexcept {
        return handle_;
    }

    /**
     * @brief Returns a pointer to the internal HANDLE for out-parameter APIs.
     * @return Pointer to the HANDLE member.
     */
    HANDLE* address_of() noexcept {
        return &handle_;
    }

    private:
        void Close() {
            if (is_valid()) {
                CloseHandle(handle_);
                handle_ = INVALID_HANDLE_VALUE;
            }
        }

        HANDLE handle_;
    };

} // namespace rj2xcl
