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

#include <deque>
#include <string>
#include <vector>
#include <sstream>
#include <iostream>

#include <SDKDDKVer.h>
#include <windows.h>
#include <process.h>

#include "SafePipeHandle.h"

/**
 * Pipe — Named pipe wrapper for IPC between XLL and child processes.
 *
 * NOTE: Pipe implementations in XLL and ControlR have diverged during development.
 * Unification is desirable but not blocking. If cross-platform support is needed,
 * consider adding PB framing with a magic header for packet management.
 */

#include "Constants.h"

/**
 * @brief Named Pipe wrapper for bidirectional IPC with child processes.
 *
 * Manages a Windows Named Pipe connection including connect, read, write,
 * and reconnect operations. Used by LanguageService to communicate with
 * ControlR.exe and ControlJulia.exe via Protocol Buffers.
 */
class Pipe {

private:
  rj2xcl::ipc::SafePipeHandle handle_;
  OVERLAPPED read_io_;
  OVERLAPPED write_io_;
  DWORD buffer_size_;
  std::string name_;

  /** read buffer is a single read, limited to pipe buffer size */
  char *read_buffer_;

  /**
   * message buffer is for messages that exceed the read buffer size, they're
   * constructed over multiple reads
   */
  std::string message_buffer_;

  std::deque<std::string> write_stack_;

  bool connected_;
  bool reading_;
  bool writing_;
  bool error_;

public:

  /** @brief Returns true if the pipe is connected. */
  bool connected() { return connected_; }

  /** @brief Returns true if a read operation is in progress. */
  bool reading() { return reading_; }

  /** @brief Returns true if a write operation is in progress. */
  bool writing() { return writing_; }

  /** @brief Returns true if an error has occurred on the pipe. */
  bool error() { return error_; }

  /**
   * @brief Creates the Named Pipe and optionally waits for a client connection.
   * @param name Pipe name (without \\.\pipe\ prefix).
   * @param wait If true, blocks until a client connects.
   * @return 0 on success, Windows error code on failure.
   */
  DWORD Start(std::string name, bool wait);

  /**
   * @brief Handles a connection notification and optionally starts reading.
   * @param start_read If true, initiates the first async read operation.
   */
  void Connect(bool start_read = true);

  /**
   * @brief Reads data from the pipe into a buffer.
   * @param buffer Output: received data.
   * @param block If true, performs a blocking read.
   * @return Number of bytes read, or 0 if no data available.
   */
  DWORD Read(std::string &buffer, bool block = false);

  /**
   * @brief Queues a message for writing to the pipe.
   * @param message The message string to send.
   */
  void PushWrite(const std::string &message);

  /**
   * @brief Queues multiple messages for writing.
   * @param list Vector of message strings to send.
   */
  void QueueWrites(std::vector<std::string> &list);

  /**
   * @brief Attempts to write the next queued message.
   * @return Non-zero if data was written; 0 if no write took place or write is pending.
   */
  int NextWrite();

  /**
   * @brief Initiates an asynchronous read operation.
   * @return Non-zero on success, 0 on failure.
   */
  int StartRead();

  /** @brief Clears the error state, allowing operations to resume. */
  void ClearError();

  /**
   * @brief Disconnects and resets the pipe for a new connection.
   * @return 0 on success, Windows error code on failure.
   */
  DWORD Reset();

  /**
   * @brief Returns the full pipe name (e.g., "\\\\.\\pipe\\rj2xcl_R_0").
   * @return Full pipe path string.
   */
  std::string full_name();

  /**
   * @brief Returns the event handle signaled when a read completes.
   * @return HANDLE for use with WaitForMultipleObjects.
   */
  HANDLE wait_handle_read();

  /**
   * @brief Returns the event handle signaled when a write completes.
   * @return HANDLE for use with WaitForMultipleObjects.
   */
  HANDLE wait_handle_write();

  /**
   * @brief Returns the pipe buffer size in bytes.
   * @return Buffer size.
   */
  DWORD buffer_size();

  /**
   * @brief Returns the raw pipe HANDLE for WaitForMultipleObjects.
   * @return Raw Windows HANDLE.
   */
  HANDLE pipe_handle();

public:
  Pipe();
  ~Pipe();

};



