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

#include "variable.pb.h"
#include "UniqueHandle.h"
#include <mutex>

/**
 * @brief Shared state for XLL callback communication between threads.
 *
 * Contains synchronization events and Protobuf buffers used to pass
 * callback requests from language service threads to the Excel UI thread.
 */
class CallbackInfo {
public:
  rj2xcl::UniqueHandle default_unsignaled_event_;   ///< Event initially unsignaled (for blocking waits)
  rj2xcl::UniqueHandle default_signaled_event_;     ///< Event initially signaled (for immediate pass-through)
  RJ2XCLBuffers::CallResponse callback_call_;       ///< Protobuf buffer for incoming callback request
  RJ2XCLBuffers::CallResponse callback_response_;   ///< Protobuf buffer for callback response

  /// Mutex protecting callback_call_ and callback_response_ from concurrent access
  std::mutex callback_mutex_;

public:
  /** @brief Constructs CallbackInfo and creates the synchronization events. */
  CallbackInfo() {
    default_signaled_event_.reset(CreateEvent(0, TRUE, TRUE, 0));
    default_unsignaled_event_.reset(CreateEvent(0, TRUE, FALSE, 0));
  }

  ~CallbackInfo() {
    // UniqueHandle automagically closes handles
  }

};

