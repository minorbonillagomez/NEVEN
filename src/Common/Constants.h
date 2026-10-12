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

#include <cstdint>

namespace rj2xcl {

/**
 * @brief Centralized constants for the RJ2XCL system.
 *
 * Replaces scattered #define macros and magic numbers across:
 *   - pipe.h (DEFAULT_BUFFER_SIZE, MAX_PIPE_COUNT)
 *   - controlr.h (CALLBACK_INDEX, PRIMARY_CLIENT_INDEX)
 *   - control_python.cc (kCallbackIndex, kPrimaryClientIndex, kMaxPipeCount)
 *   - file_change_watcher.h (FILE_WATCH_LOOP_DEBOUNCE_TIMEOUT, FILE_WATCH_LOOP_NORMAL_TIMEOUT)
 *   - language_service.h (PIPE_BUFFER_SIZE)
 *
 * All values use C++17 inline constexpr — resolved at compile time with
 * zero runtime cost and no macro namespace pollution.
 */
namespace Constants {

    // ─── Pipe Configuration ─────────────────────────────────────────

    /** @brief Default buffer size for Named Pipe read/write operations (8 KB).
     *
     *  Replaces DEFAULT_BUFFER_SIZE in pipe.h and PIPE_BUFFER_SIZE in
     *  language_service.h.
     */
    inline constexpr uint32_t kPipeBufferSize = 8 * 1024;

    /** @brief Maximum concurrent pipe connections per language process.
     *
     *  Passed to CreateNamedPipeA as nMaxInstances.
     *  Replaces MAX_PIPE_COUNT in pipe.h.
     */
    inline constexpr int kMaxPipeCount = 4;

    /** @brief Pipe index for the callback channel (XLL → ControlX).
     *
     *  Replaces CALLBACK_INDEX in controlr.h and kCallbackIndex in
     *  control_python.cc.
     */
    inline constexpr int kCallbackPipeIndex = 0;

    /** @brief Pipe index for the primary client connection.
     *
     *  Replaces PRIMARY_CLIENT_INDEX in controlr.h and
     *  kPrimaryClientIndex in control_python.cc.
     */
    inline constexpr int kPrimaryClientPipeIndex = 1;

    // ─── Timeouts ───────────────────────────────────────────────────

    /** @brief Default call timeout in milliseconds (10 minutes).
     *
     *  Used by ConfigService::GetCallTimeoutMs() as the fallback when
     *  the config file does not specify a value.
     */
    inline constexpr uint32_t kDefaultCallTimeoutMs = 600'000;

    /** @brief Maximum allowed call timeout in milliseconds (30 minutes).
     *
     *  ConfigService clamps callTimeoutMs to this ceiling.
     */
    inline constexpr uint32_t kMaxCallTimeoutMs = 1'800'000;

    /** @brief File loading timeout during startup in milliseconds (30 seconds).
     *
     *  Applied via LanguageService::SetLoadingTimeout() while source
     *  files are being read at startup.
     */
    inline constexpr uint32_t kFileLoadingTimeoutMs = 30'000;

    /** @brief File watch debounce timeout in milliseconds.
     *
     *  Replaces FILE_WATCH_LOOP_DEBOUNCE_TIMEOUT in file_change_watcher.h.
     *  Duplicate filesystem notifications within this window are coalesced.
     */
    inline constexpr uint32_t kFileWatchDebounceMs = 150;

    /** @brief File watch normal polling interval in milliseconds.
     *
     *  Replaces FILE_WATCH_LOOP_NORMAL_TIMEOUT in file_change_watcher.h.
     */
    inline constexpr uint32_t kFileWatchNormalMs = 500;

    /** @brief Pipe connection retry delay in milliseconds.
     *
     *  Default timeout passed to CreateNamedPipeA for client connection
     *  wait.
     */
    inline constexpr uint32_t kPipeRetryDelayMs = 100;

    /** @brief Maximum pipe connection retries before giving up. */
    inline constexpr int kMaxPipeConnectRetries = 30;

    // ─── Retry Limits ───────────────────────────────────────────────

    /** @brief Default max retries for pipe reconnection.
     *
     *  Used by ConfigService::GetMaxRetries() as the fallback when
     *  the config file does not specify a value.
     */
    inline constexpr int kDefaultMaxRetries = 2;

    /** @brief Maximum allowed retries (config validation ceiling).
     *
     *  ConfigService clamps maxRetries to this ceiling.
     */
    inline constexpr int kMaxRetriesCeiling = 10;

    // ─── Buffer Limits ──────────────────────────────────────────────

    /** @brief Maximum dynamic buffer growth for pipe reads (256 KB).
     *
     *  Upper bound for the dynamic read buffer in LanguageService
     *  that grows on ERROR_MORE_DATA.
     */
    inline constexpr uint32_t kMaxDynamicBufferSize = 256 * 1024;

    /** @brief Stdio buffer truncation target (8 KB).
     *
     *  When the stdio forwarding buffer exceeds this size plus a
     *  1 KB margin, TruncateBuffer() trims from the front.
     */
    inline constexpr uint32_t kStdioBufferTruncateTarget = 8 * 1024;

    // ─── Registry Keys ──────────────────────────────────────────────

    /** @brief Registry key for development options (DWORD flags). */
    inline constexpr const char* kDevOptionsRegistryKey = "RJ2XCL.DevOptions";

    // ─── Environment Variables ──────────────────────────────────────

    /** @brief Environment variable for the RJ2XCL home directory. */
    inline constexpr const char* kHomeEnvVar = "RJ2XCL_HOME";

} // namespace Constants
} // namespace rj2xcl
