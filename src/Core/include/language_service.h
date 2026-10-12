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
#include "message_utilities.h"
#include "function_descriptor.h"
#include "UniqueHandle.h"
#include "com_object_map.h"
#include "callback_info.h"
#include <vector>
#include <string>
#include <regex>

#include "windows_api_functions.h"
#include "process_exit_codes.h"

#include "json11/json11.hpp"
#include "language_desc.h"
#include "Constants.h"

/** @brief Per-language process health status. */
enum class HealthStatus {
    Healthy,      ///< Process is running and pipe is connected
    Unavailable,  ///< Process has exited or pipe is permanently broken
    Unknown       ///< Initial state before first connection attempt
};

/**
 * @brief Abstract base class for language service features.
 *
 * Manages the lifecycle of a child language process (R, Julia, Python),
 * including pipe communication, process launch, and callback handling.
 */
class LanguageService {

private:

  /** @brief Transaction ID generator for unique message sequencing. */
  static uint32_t transaction_id_;

protected:

  /**
   * @brief Returns the next unique transaction ID.
   * @return Monotonically increasing transaction ID.
   */
  static uint32_t transaction_id() { return transaction_id_++; }

  /**
   * @brief Callback thread entry point — runs COM-initialized on a separate thread.
   * @param param Pointer to the LanguageService instance.
   * @return Thread exit code (always 0).
   */
  static unsigned __stdcall CallbackThreadFunction(void *param) {
    HRESULT hr = CoInitializeEx(NULL, COINIT_APARTMENTTHREADED);
    auto language_service = reinterpret_cast<LanguageService*>(param);
    language_service->RunCallbackThread();
    CoUninitialize();
    return 0;
  }
  
protected:

  /** @brief Language descriptor containing name, prefix, and capabilities. */
  LanguageDescriptor language_descriptor_;

  /** @brief Process information handle for the child process. */
  PROCESS_INFORMATION process_info_;

  /** @brief Named Pipe name — persists for reconnection support. */
  std::string pipe_name_;

  /** @brief Communication pipe handle to the child process. */
  rj2xcl::UniqueHandle pipe_handle_;

  /** @brief Overlapped I/O event handle for non-blocking pipe operations. */
  rj2xcl::UniqueHandle io_event_handle_;

  /** @brief Overlapped structure for non-blocking I/O. */
  OVERLAPPED io_;

  /** @brief Process ID of the child language process. */
  DWORD child_process_id_;
    
  /** @brief Whether the pipe is currently connected to the child process. */
  bool connected_;

  /** @brief Whether the first call should use an extended timeout (e.g., Julia JIT). */
  bool first_call_timeout_ = true;

  /** @brief Whether the language service has been configured. */
  bool configured_;

  /** @brief Whether this language uses lazy loading (user activates on demand). */
  bool lazy_load_;

  /** @brief Override timeout for file loading operations (0 = use config default). */
  DWORD loading_timeout_ms_ = 0;

  /** @brief Dynamic read/write buffer — starts at kPipeBufferSize, grows as needed. */
  std::vector<char> buffer_;
    
  /** @brief Absolute path to the child process executable. */
  std::string child_path_;

  /** @brief Developer option flags passed from the registry. */
  DWORD dev_flags_;

  /** @brief Shared callback state — single reference across language services. */
  CallbackInfo &callback_info_;

  /** @brief COM object map for Excel automation dispatch. */
  COMObjectMap &object_map_;

  /** @brief Cached Windows Job Object handle for child process management. */
  rj2xcl::UniqueHandle job_handle_;

  /** @brief Current process health status (Unknown → Healthy → Unavailable). */
  HealthStatus health_status_ = HealthStatus::Unknown;

  /** @brief Cached per-language call timeout in milliseconds (0 = use global). */
  DWORD per_language_timeout_ms_ = 0;

public:

  /**
   * @brief Constructs a LanguageService with shared state and configuration.
   * @param callback_info Shared callback state for XLL communication.
   * @param object_map COM object map for Excel automation.
   * @param dev_flags Developer option flags from the registry.
   * @param config Main application configuration JSON.
   * @param home_directory RJ2XCL installation home path.
   * @param descriptor Language-specific descriptor JSON.
   */
  LanguageService(CallbackInfo &callback_info, COMObjectMap &object_map, DWORD dev_flags, const json11::Json &config, const std::string &home_directory, const json11::Json &descriptor);

  /** @brief Destructor. Prefer calling Shutdown() explicitly before destruction. */
  ~LanguageService() {}

public:

  /**
   * @brief Retrieves the exit code of the child process.
   * @param exit_code Pointer to receive the exit code value.
   * @return true if the exit code was retrieved, false if the process handle is invalid.
   */
  bool ProcessExitCode(DWORD *exit_code);

  /**
   * @brief Returns whether the language service has been configured.
   * @return true if configured.
   */
  bool configured() { return configured_; }

  /**
   * @brief Whether this language uses lazy loading.
   * @return true if lazy load enabled.
   */
  bool lazy_load() { return lazy_load_; }

  /**
   * @brief Returns whether the pipe is currently connected to the child process.
   * @return true if connected.
   */
  bool connected() { return connected_; }

  /**
   * @brief Returns the language prefix used in Excel formulas (e.g., "R", "J").
   * @return Language prefix string.
   */
  std::string prefix() { return language_descriptor_.prefix_;  }

  /**
   * @brief Returns the display name of the language (e.g., "R", "Julia").
   * @return Language name string.
   */
  std::string name() { return language_descriptor_.name_; }

  /**
   * @brief Returns the current health status of the child process.
   * @return HealthStatus enum value (Healthy, Unavailable, or Unknown).
   */
  HealthStatus GetHealthStatus() const { return health_status_; }

  /**
   * @brief Returns the Named Pipe name used for IPC with the child process.
   * @return Pipe name string.
   */
  std::string pipe_name() { return pipe_name_; }

  /**
   * @brief Returns whether the language supports named arguments in function calls.
   * @return true if named arguments are supported.
   */
  bool named_arguments() { return language_descriptor_.named_arguments_;  }

  /**
   * @brief Sets a temporary timeout override for file loading operations.
   * @param ms Timeout in milliseconds (0 = use config default).
   */
  void SetLoadingTimeout(DWORD ms) { loading_timeout_ms_ = ms; }

protected:

  /**
   * @brief Launches the child language process within a Windows Job Object.
   * @param job_handle Handle to the Job Object for process management.
   * @param command_line Command line string for the child process.
   * @return 0 on success, non-zero error code on failure.
   */
  int LaunchProcess(HANDLE job_handle, char *command_line);

public:

  /**
   * @brief Reads and loads a source file into the language runtime.
   *
   * Sends a "read-source-file" command to the child process via the pipe.
   * @param file Path to the source file to load.
   */
  virtual void ReadSourceFile(const std::string &file);

  /**
   * @brief Checks whether this language service can process a file based on its extension.
   * @param path File path to check.
   * @return true if the file extension matches this language.
   */
  virtual bool ValidFile(const std::string &path);

  /**
   * @brief Starts the child language process.
   * @param job_handle Windows Job Object handle for process management.
   * @return 0 on success, non-zero error code on failure.
   */
  virtual int StartChildProcess(HANDLE job_handle);

  /**
   * @brief Connects to the child process via Named Pipe.
   * @param job_handle Windows Job Object handle (used if process needs restart).
   */
  virtual void Connect(HANDLE job_handle);

  /** @brief Sends initialization commands to the connected language runtime. */
  virtual void Initialize();

  /** @brief Gracefully shuts down the child process and releases resources. */
  virtual void Shutdown();

  /** @brief Runs the callback thread loop for XLL callback communication. */
  virtual void RunCallbackThread();

  /**
   * @brief Passes the Excel Application COM pointer to the child process.
   * @param application_pointer IDispatch pointer to the Excel Application object.
   */
  virtual void SetApplicationPointer(LPDISPATCH application_pointer);

  /**
   * @brief Configures graphics output targets for the language runtime.
   * @param application_dispatch IDispatch pointer to the Excel Application object.
   */
  virtual void SetGraphicsTargets(LPDISPATCH application_dispatch) {}

  /**
   * @brief Sets the list of files to watch for changes.
   * @param files Vector of file paths to monitor.
   */
  virtual void SetWatchFiles(const std::vector<std::string> &files) {}

  /**
   * @brief Maps language functions from the child process into Excel's function wizard.
   * @param key Numeric key identifying this language service.
   * @param language_service Shared pointer to this language service instance.
   * @return List of function descriptors for Excel registration.
   */
  virtual FUNCTION_LIST MapLanguageFunctions(uint32_t key, std::shared_ptr<LanguageService> language_service);

  /**
   * @brief Dispatches a function call to the child language process.
   * @param response Protobuf response to populate with the result.
   * @param call Protobuf call containing function name and arguments.
   */
  virtual void Call(RJ2XCLBuffers::CallResponse &response, RJ2XCLBuffers::CallResponse &call);

  /**
   * @brief Performs variable interpolation on a string using language-specific patterns.
   * @param str String to interpolate (modified in place).
   * @param additional_replacements Optional extra key-value pairs for substitution.
   */
  virtual void InterpolateString(std::string &str, const std::vector<std::pair<std::string, std::string>> &additional_replacements = {});

public:

  /**
   * @brief Creates a function list from a Protobuf message for Excel registration.
   * @param message Protobuf message containing function descriptors.
   * @param key Numeric key identifying the language service.
   * @param name Language display name.
   * @param service_pointer Shared pointer to the language service.
   * @return List of function descriptors.
   */
  static FUNCTION_LIST CreateFunctionList(const RJ2XCLBuffers::CallResponse &message, uint32_t key, const std::string &name, std::shared_ptr<LanguageService> service_pointer);

};
