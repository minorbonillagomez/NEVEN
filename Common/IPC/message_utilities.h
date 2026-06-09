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

#include <string>
#include <sstream>

#include "variable.pb.h"

// #define INCLUDE_DUMP_JSON

#ifdef INCLUDE_DUMP_JSON
#include <google\protobuf\util\json_util.h>
#endif

/**
 * @brief Utilities for Protocol Buffer message framing and type inspection.
 *
 * Provides frame/unframe operations for length-prefixed Protobuf messages
 * used in Named Pipe IPC, and type-checking utilities for arrays.
 */

namespace MessageUtilities {

  /** @brief Bitmask flags for Protobuf array element types. */
  typedef enum {
    nil = 0x00,       ///< Null/nil values
    integer = 0x01,   ///< Integer values
    real = 0x02,      ///< Real/float values
    numeric = 0x04,   ///< Mixed integer + real (reduce to real)
    string = 0x08,    ///< String values
    logical = 0x10    ///< Boolean values
  }
  TypeFlags;

  inline TypeFlags operator | (TypeFlags a, TypeFlags b) {
    return static_cast<TypeFlags>(static_cast<uint32_t>(a) | static_cast<uint32_t>(b));
  }

  inline TypeFlags operator & (TypeFlags a, TypeFlags b) {
    return static_cast<TypeFlags>(static_cast<uint32_t>(a) & static_cast<uint32_t>(b));
  }

  /**
   * @brief Checks if a Protobuf array contains a single homogeneous type.
   *
   * Returns a bitmask indicating which types are present. The "numeric" flag
   * means the array has a mix of integers and reals (reduce to real).
   *
   * @param arr The Protobuf array to inspect.
   * @param allow_nil If true, nil values don't affect the type determination.
   * @param allow_missing If true, missing values don't affect the type determination.
   * @return TypeFlags bitmask of detected types.
   */
  TypeFlags CheckArrayType(const RJ2XCLBuffers::Array &arr, bool allow_nil = true, bool allow_missing = true);

  /**
   * @brief Deserializes a length-prefixed Protobuf message from a raw buffer.
   * @param message Output: the deserialized Protobuf message.
   * @param data Raw buffer containing the framed message.
   * @param len Total length of the buffer in bytes.
   * @return true if deserialization succeeded.
   */
  bool Unframe(google::protobuf::Message &message, const char *data, uint32_t len);

  /**
   * @brief Deserializes a length-prefixed Protobuf message from a string buffer.
   * @param message Output: the deserialized Protobuf message.
   * @param message_buffer String containing the framed message.
   * @return true if deserialization succeeded.
   */
  bool Unframe(google::protobuf::Message &message, const std::string &message_buffer);

  /**
   * @brief Serializes a Protobuf message with a 4-byte length prefix.
   * @param message The Protobuf message to serialize.
   * @return Framed message as a string (length prefix + serialized payload).
   */
  std::string Frame(const google::protobuf::Message &message);
  
#ifdef INCLUDE_DUMP_JSON

  /**
   * @brief Dumps a Protobuf message as JSON for debugging.
   * @param message The message to dump.
   * @param path Optional file path to write to (nullptr = stdout).
   */
  void DumpJSON(const google::protobuf::Message &message, const char *path = 0);

#endif


};
