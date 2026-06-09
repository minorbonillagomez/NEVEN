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
#include <google/protobuf/message.h>

namespace rj2xcl {
namespace ipc {

/**
 * @brief Validates IPC message frames before Protobuf deserialization.
 *
 * Enforces size limits and structural integrity on incoming Named Pipe
 * messages to prevent memory corruption from malformed data.
 */
class MessageValidator {
public:
    /** @brief Default maximum message size: 64 MB. */
    static constexpr uint32_t kDefaultMaxMessageSize = 64 * 1024 * 1024;

    /** @brief Minimum valid message size: 4 bytes (length prefix only). */
    static constexpr uint32_t kMinFrameSize = sizeof(uint32_t);

    /**
     * @brief Validates a framed message before deserialization.
     *
     * Checks:
     * 1. Buffer has at least 4 bytes for length prefix
     * 2. Length prefix does not exceed max_message_size
     * 3. Buffer contains enough data for the declared length
     *
     * @param data Raw buffer pointer.
     * @param buffer_len Total bytes available in buffer.
     * @param max_message_size Maximum allowed payload size.
     * @return true if frame structure is valid for deserialization attempt.
     */
    static bool ValidateFrame(const char* data, uint32_t buffer_len,
                              uint32_t max_message_size = kDefaultMaxMessageSize);

    /**
     * @brief Enhanced Unframe with validation.
     *
     * Validates frame structure, then attempts Protobuf deserialization.
     * Logs errors via LogService on failure.
     *
     * @param message Output protobuf message.
     * @param data Raw buffer.
     * @param len Buffer length.
     * @param max_message_size Maximum allowed payload.
     * @return true if successfully deserialized.
     */
    static bool SafeUnframe(google::protobuf::Message& message,
                            const char* data, uint32_t len,
                            uint32_t max_message_size = kDefaultMaxMessageSize);
};

} // namespace ipc
} // namespace rj2xcl
