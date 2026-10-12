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

#include "MessageValidator.h"
#include "../LogService.h"

#include <cstring>

namespace rj2xcl {
namespace ipc {

bool MessageValidator::ValidateFrame(const char* data, uint32_t buffer_len,
                                     uint32_t max_message_size) {
    // 1. Check data is not null
    if (data == nullptr) {
        return false;
    }

    // 2. Check buffer has at least 4 bytes for the length prefix
    if (buffer_len < kMinFrameSize) {
        return false;
    }

    // 3. Read the length prefix from the first 4 bytes (little-endian uint32_t)
    uint32_t declared_length = 0;
    std::memcpy(&declared_length, data, sizeof(uint32_t));

    // 4. Check length prefix does not exceed max_message_size
    if (declared_length > max_message_size) {
        return false;
    }

    // 5. Check buffer contains enough data for the declared length
    if (buffer_len < kMinFrameSize + declared_length) {
        return false;
    }

    // All checks passed
    return true;
}

bool MessageValidator::SafeUnframe(google::protobuf::Message& message,
                                   const char* data, uint32_t len,
                                   uint32_t max_message_size) {
    // 1. Validate frame structural integrity
    if (!ValidateFrame(data, len, max_message_size)) {
        RJ2XCL_LOG_ERR("[MessageValidator] SafeUnframe: frame validation failed (len=%u)", len);
        return false;
    }

    // 2. Read the declared payload length from the first 4 bytes
    uint32_t declared_length = 0;
    std::memcpy(&declared_length, data, sizeof(uint32_t));

    // 3. Attempt Protobuf deserialization on the payload
    if (!message.ParseFromArray(data + sizeof(uint32_t), static_cast<int>(declared_length))) {
        RJ2XCL_LOG_ERR("[MessageValidator] SafeUnframe: ParseFromArray failed (declared_length=%u)", declared_length);
        return false;
    }

    return true;
}

} // namespace ipc
} // namespace rj2xcl
