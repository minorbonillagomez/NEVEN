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
#include "variable.pb.h"

/**
 * @brief Initialize the Python interpreter and execute startup.py.
 * @param config_path Path to the RJ2XCL home directory (for locating startup.py).
 *
 * Reads startup.py from the startup directory and executes it via
 * PyRun_SimpleString(). Includes a retry loop (max 3 attempts) with
 * PyErr_Clear() + Sleep(100) between retries.
 */
void PythonInit(const std::string& config_path);

/**
 * @brief Returns whether startup.py executed successfully.
 * @return true if startup succeeded, false if all retries were exhausted.
 */
bool PythonStartupSucceeded();

/**
 * @brief Execute arbitrary Python code.
 * @param response Protobuf response to populate with results.
 * @param call Protobuf call containing the code to execute.
 */
void PythonExec(RJ2XCLBuffers::CallResponse& response, const RJ2XCLBuffers::CallResponse& call);

/**
 * @brief Call a named Python function with protobuf arguments.
 * @param response Protobuf response to populate with results.
 * @param call Protobuf call containing function name and arguments.
 */
void PythonCall(RJ2XCLBuffers::CallResponse& response, const RJ2XCLBuffers::CallResponse& call);

/**
 * @brief Execute Python code in shell mode (captures stdout).
 * @param command The Python code to execute.
 * @param shell_buffer Buffer for accumulating multi-line input.
 * @return 0 on success, non-zero on error.
 */
int PythonShellExec(const std::string& command, std::string& shell_buffer);

/**
 * @brief List registered Python functions for Excel integration.
 * @param response Protobuf response to populate with function list.
 * @param call Protobuf call (may contain directory filter).
 */
void ListScriptFunctions(RJ2XCLBuffers::CallResponse& response, const RJ2XCLBuffers::CallResponse& call);

/**
 * @brief Read and execute a Python source file.
 * @param file Path to the .py file.
 * @param notify Whether to send a notification on completion.
 * @return true if the file was read and executed successfully.
 */
bool ReadSourceFile(const std::string& file, bool notify = false);

/**
 * @brief Callback function for Python → XLL communication.
 */
bool Callback(const RJ2XCLBuffers::CallResponse& call, RJ2XCLBuffers::CallResponse& response);

/**
 * @brief Push a message to the console client.
 */
void PushConsoleMessage(google::protobuf::Message& message);
