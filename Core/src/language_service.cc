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

#include "stdafx.h"
#include "XLCALL.H"
#include "variable.pb.h"
#include "rj2xcl.h"
#include "language_service.h"
#include "string_utilities.h"
#include "DiscoveryService.h"
#include "SecurityService.h"
#include "ConfigService.h"
#include "LogService.h"
#include "DiagnosticRouter.h"
#include "IPC/MessageValidator.h"
#include <array>

// by convention we don't use transaction 0. 
// this may cause a problem if it rolls over.
uint32_t LanguageService::transaction_id_ = 1;

//LanguageService::LanguageService(CallbackInfo &callback_info, COMObjectMap &object_map, DWORD dev_flags, const json11::Json &config, const std::string &home_directory, const LanguageDescriptor &descriptor)
LanguageService::LanguageService(CallbackInfo &callback_info, COMObjectMap &object_map, DWORD dev_flags, const json11::Json &config, const std::string &home_directory, const json11::Json &json)
  : callback_info_(callback_info)
  , object_map_(object_map)
  , dev_flags_(dev_flags)
  , connected_(false)
  , configured_(false)
  , lazy_load_(false)
  , buffer_(rj2xcl::Constants::kPipeBufferSize)    // H5: initialize dynamic buffer
{
  memset(&io_, 0, sizeof(io_));

  // we're now receiving the json descriptor instead of the object, but we still
  // want to construct the object. the json descriptor may have multiple versions
  // for a given language; in that case, we want to overlay and compare.

  language_descriptor_.FromJSON(json, home_directory);

  // comment out language (or delete) to deactivate.
  
  configured_ = !(config["NEVEN"][language_descriptor_.name_].is_null());
  if (!configured_) return;

  // Allow disabling a language via "enabled": false in neven-config.json
  // e.g. "Julia": { "home": "", "enabled": false }
  // If the key is missing, the language is enabled by default.
  if (config["NEVEN"][language_descriptor_.name_]["enabled"].is_bool() &&
      !config["NEVEN"][language_descriptor_.name_]["enabled"].bool_value()) {
      configured_ = false;
      RJ2XCL_LOG_INFO("Language '%s' disabled via configuration (enabled: false)",
          language_descriptor_.name_.c_str());
      return;
  }

  // Support lazy loading: language is configured but not auto-connected
  // User activates it on demand via =NEVEN.iniciar.J()
  if (config["NEVEN"][language_descriptor_.name_]["lazyLoad"].is_bool() &&
      config["NEVEN"][language_descriptor_.name_]["lazyLoad"].bool_value()) {
      lazy_load_ = true;
      RJ2XCL_LOG_INFO("Language '%s' configured for lazy loading (user activates on demand)",
          language_descriptor_.name_.c_str());
  }

  std::string override_home;
  if (config["NEVEN"][language_descriptor_.name_]["home"].is_string()) {
      override_home = config["NEVEN"][language_descriptor_.name_]["home"].string_value();
  }

  std::string tag;
  if (config["NEVEN"][language_descriptor_.name_]["tag"].is_string()) {
      tag = config["NEVEN"][language_descriptor_.name_]["tag"].string_value();
  }

  // Use DiscoveryService to find the best installation
  auto installation = rj2xcl::DiscoveryService::Instance().GetBestVersion(
      language_descriptor_.name_, tag, override_home);

  if (!installation.home_path.empty()) {
      language_descriptor_.home_ = installation.home_path;
      configured_ = true;
      RJ2XCL_LOG_INFO("Discovered %s version %s at %s", 
          language_descriptor_.name_.c_str(), 
          installation.version.c_str(), 
          installation.home_path.c_str());
  } else {
      configured_ = false;
      RJ2XCL_LOG_ERR("Failed to discover %s installation", language_descriptor_.name_.c_str());
      return;
  }

  DWORD result = ExpandEnvironmentStringsA(language_descriptor_.home_.c_str(), 0, 0);
  if (result) {
    char *buffer = new char[result + 1];
    result = ExpandEnvironmentStringsA(language_descriptor_.home_.c_str(), buffer, result + 1);
    if (result) language_descriptor_.home_ = buffer;
    delete[] buffer;
  }

  child_path_ = home_directory;
  child_path_.append("\\");
  child_path_.append(language_descriptor_.executable_);

  if (dev_flags_) {
    std::string override_key = "RJ2XCL2.Override$NAMEPipeName";
    InterpolateString(override_key);
    APIFunctions::GetRegistryString(pipe_name_, override_key.c_str());
  }

  if (!pipe_name_.length()) {
    std::stringstream ss;
    ss << "RJ2XCL2-PIPE-" << language_descriptor_.prefix_ << "-" << _getpid();
    pipe_name_ = ss.str();
  }

  // Cache per-language timeout from config
  per_language_timeout_ms_ = rj2xcl::ConfigService::Instance()
      .GetLanguageCallTimeoutMs(language_descriptor_.name_);

}

void LanguageService::Initialize() {

  if (connected_) {
    // Callback thread — enables R/Julia to call back into Excel
    // (insert graphics, write cells, execute COM automation)
    // Note: Disabled for Python — the callback pipe breaks immediately after connect
    // due to a timing issue in ControlPython.exe. Python doesn't use COM callbacks.
    bool skip_callback = (language_descriptor_.name_ == "Python");
    if (!skip_callback) {
        uintptr_t callback_thread_ptr = _beginthreadex(0, 0, CallbackThreadFunction, this, 0, 0);
        if (callback_thread_ptr) {
            RJ2XCL_LOG_INFO("Callback thread started for %s", language_descriptor_.name_.c_str());
        } else {
            RJ2XCL_LOG_WARN("Callback thread failed to start for %s", language_descriptor_.name_.c_str());
        }
    } else {
        RJ2XCL_LOG_INFO("Callback thread skipped for %s (not needed)", language_descriptor_.name_.c_str());
    }

    // get embedded startup code, split into lines
    if (language_descriptor_.startup_resource_path_.length()){

      std::string startup_code;
      auto result = APIFunctions::FileContents(language_descriptor_.startup_resource_path_);
      if (!result.is_success()) {
        RJ2XCL_LOG_ERR("LanguageService: Failed to load startup code for %s", language_descriptor_.name_.c_str());
        return;
      }
      startup_code = result.value();

      std::vector<std::string> lines;
      StringUtilities::Split(startup_code, '\n', 1, lines, true);

      RJ2XCLBuffers::CallResponse call, response;

      // R: wait=true (fast startup, keeps pipe synchronized)
      // Julia: wait=false (JIT or module re-eval would block Excel)
      bool is_julia = (language_descriptor_.name_ == "Julia");
      call.set_wait(!is_julia);
      auto code = call.mutable_code();

      // Python: send entire startup code as a single block to preserve
      // blank lines, indentation, and docstrings (Python is whitespace-sensitive)
      bool is_python = (language_descriptor_.name_ == "Python");
      if (is_python) {
          code->add_line(startup_code);
      } else {
          // R and Julia: send line-by-line (existing behavior, unchanged)
          for (auto line : lines) {
              if (line.length() > 0) {
                  RJ2XCL_LOG_DEBUG("Startup script line: %s", line.c_str());
                  code->add_line(line);
              }
          }
      }

      // added this flag to support post-init, without requiring a separate transaction

      code->set_startup(true);
      Call(response, call);

    }
  }

}

void LanguageService::SetApplicationPointer(LPDISPATCH application_pointer) {
  RJ2XCLBuffers::CallResponse call, response;

  auto function_call = call.mutable_function_call();
  function_call->set_function("install-application-pointer"); // generic
  function_call->set_target(RJ2XCLBuffers::CallTarget::system);
  object_map_.DispatchToVariable(function_call->add_arguments(), application_pointer, true);

  Call(response, call);
}

void LanguageService::RunCallbackThread() {

  // H5: Dynamic pipe buffer — starts at 8KB, grows on ERROR_MORE_DATA
  // Eliminates silent truncation of DataFrames > 8KB
  static constexpr DWORD kInitialBufferSize = 1024 * 8;
  std::vector<char> buffer(kInitialBufferSize);

  std::stringstream ss;
  ss << "\\\\.\\pipe\\" << pipe_name_ << "-CB";

  auto engine = RJ2XCL_Engine::Instance();

  HANDLE callback_pipe_handle = CreateFileA(ss.str().c_str(), GENERIC_READ | GENERIC_WRITE, 0, 0, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL | FILE_FLAG_OVERLAPPED, 0);
  if (!callback_pipe_handle || callback_pipe_handle == INVALID_HANDLE_VALUE) {
    DWORD err = GetLastError();
    RJ2XCL_LOG_ERR("err opening pipe [1]: %d", err);
  }
  else {

    RJ2XCL_LOG_INFO("Connected to callback pipe");

    DWORD mode = PIPE_READMODE_MESSAGE;
    SetNamedPipeHandleState(callback_pipe_handle, &mode, 0, 0);

    DWORD bytes = 0;
    OVERLAPPED io;

    std::string message_buffer;

    memset(&io, 0, sizeof(io));
    rj2xcl::UniqueHandle event_handle(CreateEvent(0, TRUE, FALSE, 0));
    io.hEvent = event_handle.get();
    ReadFile(callback_pipe_handle, buffer.data(), (DWORD)buffer.size(), 0, &io);
    while (true) {
      DWORD result = WaitForSingleObject(io.hEvent, 1000);
      if (result == WAIT_OBJECT_0) {
        ResetEvent(io.hEvent);
        DWORD rslt = GetOverlappedResult(callback_pipe_handle, &io, &bytes, FALSE);
        if (rslt) {

          RJ2XCLBuffers::CallResponse &call = callback_info_.callback_call_;
          RJ2XCLBuffers::CallResponse &response = callback_info_.callback_response_;

          call.Clear();
          response.Clear();

          if (message_buffer.length()) {
            message_buffer.append(buffer.data(), bytes);
            if (!rj2xcl::ipc::MessageValidator::SafeUnframe(call, message_buffer.c_str(), (uint32_t)message_buffer.length())) {
              RJ2XCL_LOG_ERR("[Callback] SafeUnframe failed on accumulated message (len=%u)", (uint32_t)message_buffer.length());
              message_buffer.clear();
              ResetEvent(io.hEvent);
              ReadFile(callback_pipe_handle, buffer.data(), (DWORD)buffer.size(), 0, &io);
              continue;
            }
            message_buffer.clear();
          }
          else {
            if (!rj2xcl::ipc::MessageValidator::SafeUnframe(call, buffer.data(), bytes)) {
              RJ2XCL_LOG_ERR("[Callback] SafeUnframe failed on direct read (bytes=%u)", bytes);
              ResetEvent(io.hEvent);
              ReadFile(callback_pipe_handle, buffer.data(), (DWORD)buffer.size(), 0, &io);
              continue;
            }
          }

          // ─── Diagnostic Stream: kConsole intercept DISABLED ─────────
          // NOTE: Intercepting kConsole here caused hangs during R startup
          // because R sends many console messages (prompt, package loading)
          // and the DiagnosticRouter.Route() call from this thread can
          // deadlock with the STA thread. R/Julia diagnostic stream requires
          // a different approach (piggybacked on response, like Python).
          // Python diagnostics still work via console_output fields.

          engine->HandleCallback(language_descriptor_.name_);

          if (call.wait()) {
            std::string str_response = MessageUtilities::Frame(response);
            WriteFile(callback_pipe_handle, str_response.c_str(), (int32_t)str_response.size(), &bytes, &io);
            result = GetOverlappedResult(callback_pipe_handle, &io, &bytes, TRUE);
          }

          // restart
          ResetEvent(io.hEvent);
          ReadFile(callback_pipe_handle, buffer.data(), (DWORD)buffer.size(), 0, &io);

        }
        else {
          DWORD err = GetLastError();
          if (err == ERROR_MORE_DATA) {
            // Accumulate partial message; grow buffer for next read if needed
            message_buffer.append(buffer.data(), bytes);
            if (buffer.size() < 1024 * 256) buffer.resize(buffer.size() * 2);
            ResetEvent(io.hEvent);
            ReadFile(callback_pipe_handle, buffer.data(), (DWORD)buffer.size(), 0, &io);
          }
          else {
            RJ2XCL_LOG_ERR("ERR in GORE: %d", err);
            // Don't break on broken pipe — try to reconnect the callback pipe
            if (err == ERROR_BROKEN_PIPE || err == ERROR_NO_DATA) {
              RJ2XCL_LOG_WARN("Callback pipe broken, attempting to reconnect...");
              CloseHandle(callback_pipe_handle);
              Sleep(500);
              callback_pipe_handle = CreateFileA(ss.str().c_str(), GENERIC_READ | GENERIC_WRITE, 0, 0, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL | FILE_FLAG_OVERLAPPED, 0);
              if (callback_pipe_handle && callback_pipe_handle != INVALID_HANDLE_VALUE) {
                DWORD mode2 = PIPE_READMODE_MESSAGE;
                SetNamedPipeHandleState(callback_pipe_handle, &mode2, 0, 0);
                ResetEvent(io.hEvent);
                ReadFile(callback_pipe_handle, buffer.data(), (DWORD)buffer.size(), 0, &io);
                RJ2XCL_LOG_INFO("Callback pipe reconnected");
              } else {
                RJ2XCL_LOG_ERR("Callback pipe reconnect failed: %d", GetLastError());
                break;
              }
            } else {
              break;
            }
          }
        }
      }
      else if (result != WAIT_TIMEOUT) {
        RJ2XCL_LOG_ERR("callback pipe error: %d", GetLastError());
        break;
      }
    }

  }
  // RESOLVED: H5 — vector<char> via RAII; no manual delete needed
}

int LanguageService::LaunchProcess(HANDLE job_handle, char *command_line) {

  STARTUPINFOA si;

  ZeroMemory(&si, sizeof(si));
  si.cb = sizeof(si);

  ZeroMemory(&process_info_, sizeof(process_info_));

  int result = 0;

  DWORD creation_flags = CREATE_NO_WINDOW;
  if (dev_flags_ & 0x01) creation_flags = CREATE_NEW_CONSOLE;

  RJ2XCL_LOG_DEBUG("CreateProcessA command line: %s", command_line);
  RJ2XCL_LOG_DEBUG("dev_flags: %d, creation_flags: %d", dev_flags_, creation_flags);

  if (!CreateProcessA(0, command_line, 0, 0, FALSE, creation_flags, 0, 0, &si, &process_info_))
  {
    DWORD err = GetLastError();
    RJ2XCL_LOG_ERR("CreateProcessA failed: %d", err);
    RJ2XCL_LOG_ERR("CreateProcess failed (%d).", err);
    result = err;
  }
  else {
    child_process_id_ = process_info_.dwProcessId;
    if (job_handle) {
      if (!AssignProcessToJobObject(job_handle, process_info_.hProcess))
      {
        RJ2XCL_LOG_ERR("Could not AssignProcessToObject");
      }
    }
  }

  return result;
}

bool LanguageService::ProcessExitCode(DWORD *exit_code) {
  return GetExitCodeProcess(process_info_.hProcess, exit_code) ? true : false;
}

void LanguageService::Connect(HANDLE job_handle) {

  if (job_handle) {
      HANDLE duplicated_handle = nullptr;
      if (DuplicateHandle(GetCurrentProcess(), job_handle, GetCurrentProcess(), &duplicated_handle, 0, FALSE, DUPLICATE_SAME_ACCESS)) {
          job_handle_.reset(duplicated_handle);
      }
  }
  int rslt = StartChildProcess(job_handle_.get());
  int errs = 0;

  // H5: buffer_ is a std::vector<char> initialized in the constructor — no manual allocation needed
  io_event_handle_.reset(CreateEvent(0, TRUE, TRUE, 0));
  io_.hEvent = io_event_handle_.get();

  if (!rslt) {

    std::string full_name = "\\\\.\\pipe\\";
    full_name.append(pipe_name_);

    while (1) {
      pipe_handle_.reset(CreateFileA(full_name.c_str(), GENERIC_READ | GENERIC_WRITE, 0, 0, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL | FILE_FLAG_OVERLAPPED, 0));
      if (!pipe_handle_.is_valid()) {

        DWORD exit_code = 0;
        if (!GetExitCodeProcess(process_info_.hProcess, &exit_code)) {
          RJ2XCL_LOG_ERR("GetExitCodeProcess failed: error %d", GetLastError());
        }
        else if (exit_code != STILL_ACTIVE) {
          RJ2XCL_LOG_ERR("Child process exited prematurely! Exit code: %d, Pipe: %s, Retries: %d",
              exit_code, full_name.c_str(), errs);
          health_status_ = HealthStatus::Unavailable;
          break;
        }

        DWORD err = GetLastError();
        RJ2XCL_LOG_ERR("err opening pipe [2]: %d", err);
        if (errs++ > 30) {
          health_status_ = HealthStatus::Unavailable;
          break;
        }
        Sleep(100);
      }
      else {
        DWORD mode = PIPE_READMODE_MESSAGE;
        BOOL state = SetNamedPipeHandleState(pipe_handle_, &mode, 0, 0);
        connected_ = true;
        health_status_ = HealthStatus::Healthy;
        RJ2XCL_LOG_INFO("Pipe connected OK! Language: %s, Pipe: %s, Retries: %d",
            language_descriptor_.name_.c_str(), full_name.c_str(), errs);
        break;
      }
    }
  }

}

void LanguageService::ReadSourceFile(const std::string &file) {

  // Security: Integrity Check
  if (!rj2xcl::SecurityService::Instance().VerifyScriptIntegrity(file)) {
      RJ2XCL_LOG_ERR("Security violation: Script integrity check failed for %s", file.c_str());
      return;
  }

  RJ2XCLBuffers::CallResponse call, response;
  call.set_wait(true); // prevent race

  auto function_call = call.mutable_function_call();
  function_call->set_function("read-source-file");
  function_call->set_target(RJ2XCLBuffers::CallTarget::system);
  function_call->add_arguments()->set_str(file);
  function_call->add_arguments()->set_boolean(true); // notify

  Call(response, call);

}

void LanguageService::InterpolateString(std::string &str, const std::vector<std::pair<std::string, std::string>> &additional_replacements){

  auto replace_function = [](std::string &haystack, std::string needle, std::string replacement) {
    for (std::string::size_type i = 0; (i = haystack.find(needle, i)) != std::string::npos;)
    {
      haystack.replace(i, needle.length(), replacement);
      i += replacement.length();
    }
  };
  
  // x64 only — 32-bit is not supported
#ifdef _WIN64
  const char arch[] = "x64";
#else
  const char arch[] = "i386";
#endif

  replace_function(str, "$HOME", language_descriptor_.home_);
  replace_function(str, "$ARCH", arch);
  replace_function(str, "$NAME", language_descriptor_.name_);

  for (const auto &pair : additional_replacements) {
    replace_function(str, pair.first, pair.second);
  }

}

bool LanguageService::ValidFile(const std::string &file) {

  std::array<char, MAX_PATH> path_arr{};
  char* path = path_arr.data();

  size_t len = file.length();
  if (len > MAX_PATH - 2) len = MAX_PATH - 2;
  memcpy(path, file.c_str(), len);
  path[len] = 0;

  char *extension = PathFindExtensionA(path);
  if (extension && *extension) {
    // extension includes the dot, e.g. ".r", ".jl"
    // Convert to lowercase for comparison
    std::string ext_lower = extension + 1; // skip the dot
    std::transform(ext_lower.begin(), ext_lower.end(), ext_lower.begin(), ::tolower);
    for (const auto& lang_ext : language_descriptor_.extensions_) {
      std::string lang_ext_lower = lang_ext;
      std::transform(lang_ext_lower.begin(), lang_ext_lower.end(), lang_ext_lower.begin(), ::tolower);
      if (ext_lower == lang_ext_lower) return true;
    }
  }

  return false;
}

void LanguageService::Shutdown() {

  if (connected_) {
    RJ2XCLBuffers::CallResponse call;
    RJ2XCLBuffers::CallResponse rsp;

    call.set_wait(false);
    call.mutable_function_call()->set_function("shutdown");
    call.mutable_function_call()->set_target(RJ2XCLBuffers::CallTarget::system);
    Call(rsp, call);

    connected_ = false;
    pipe_handle_.reset();
  }
}

/**
 * @brief Sends a message to the language service and optionally waits for response.
 * 
 * This is the core IPC function. It serializes the call via Protobuf,
 * writes to the Named Pipe, and reads the response. Handles reconnection
 * on pipe failure (max retries from config). For Julia, the first call
 * may take several minutes due to JIT compilation.
 * 
 * @param response Output: the response from R/Julia
 * @param call Input: the request to send (code, function call, etc.)
 */
void LanguageService::Call(RJ2XCLBuffers::CallResponse &response, RJ2XCLBuffers::CallResponse &call) {

  bool reconnected = false;
  int retry_count = 0;
  const int MAX_RETRIES = rj2xcl::ConfigService::Instance().GetMaxRetries();

retry:
  if (retry_count++ > MAX_RETRIES) {
    response.set_err("max retries");
    return;
  }
  DWORD bytes;
  uint32_t id = LanguageService::transaction_id();
  auto engine = RJ2XCL_Engine::Instance();

  call.set_id(id);
  std::string framed_message = MessageUtilities::Frame(call);

  if (!connected_) {
      if (!reconnected && job_handle_) {
          Connect(job_handle_);
          Initialize();
          reconnected = true; goto retry;
      }
      response.set_err("not connected");
      return;
  }

  ResetEvent(io_.hEvent);
  if (!WriteFile(pipe_handle_, framed_message.c_str(), (int32_t)framed_message.length(), NULL, &io_)) {
      DWORD err = GetLastError();
      if (err != ERROR_IO_PENDING) {
          if (!reconnected && (err == ERROR_BROKEN_PIPE || err == ERROR_NO_DATA) && job_handle_.is_valid()) {
              connected_ = false;
              pipe_handle_.reset();
              Connect(job_handle_.get());
              Initialize();
              reconnected = true; goto retry;
          }
          response.set_err("write error");
          return;
      }
  }

  if (!GetOverlappedResult(pipe_handle_, &io_, &bytes, TRUE)) {
      DWORD err = GetLastError();
      if (!reconnected && (err == ERROR_BROKEN_PIPE || err == ERROR_NO_DATA) && job_handle_.is_valid()) {
          connected_ = false;
          pipe_handle_.reset();
          Connect(job_handle_.get());
          Initialize();
          reconnected = true; goto retry;
      }
  }

  if (call.wait()) {

    ResetEvent(io_.hEvent);
    ReadFile(pipe_handle_, buffer_.data(), (DWORD)buffer_.size(), 0, &io_);

    std::string message_buffer;
    while (true) {
      DWORD timeout_ms = loading_timeout_ms_ > 0 ? loading_timeout_ms_ : rj2xcl::ConfigService::Instance().GetCallTimeoutMs();
      DWORD signaled = WaitForSingleObject(io_.hEvent, timeout_ms);
      if (signaled == WAIT_OBJECT_0) {
        ResetEvent(io_.hEvent);
        if (GetOverlappedResult(pipe_handle_, &io_, &bytes, TRUE)) {
          if (message_buffer.length()) {
            message_buffer.append(buffer_.data(), bytes);
            if (!rj2xcl::ipc::MessageValidator::SafeUnframe(response, message_buffer.c_str(), (uint32_t)message_buffer.length())) {
              response.set_err("parse error (0x10)");
              break;
            }
          }
          else {
            if (!rj2xcl::ipc::MessageValidator::SafeUnframe(response, buffer_.data(), bytes)) {
              response.set_err("parse error (0x10)");
              break;
            }
          }

          bool complete = false;
          switch (response.operation_case()) {
          case RJ2XCLBuffers::CallResponse::OperationCase::kFunctionCall:
            engine->HandleCallbackOnThread(language_descriptor_.name_, &response);
            ResetEvent(io_.hEvent);
            framed_message = MessageUtilities::Frame(callback_info_.callback_response_);
            WriteFile(pipe_handle_, framed_message.c_str(), (int32_t)framed_message.length(), NULL, &io_);
            GetOverlappedResult(pipe_handle_, &io_, &bytes, TRUE);
            ResetEvent(io_.hEvent);
            ReadFile(pipe_handle_, buffer_.data(), (DWORD)buffer_.size(), 0, &io_);
            break;
          default:
            complete = true;
            break;
          }
          if (complete) break;
        }
        else {
          DWORD err = GetLastError();
          if (err == ERROR_MORE_DATA) {
            message_buffer.append(buffer_.data(), bytes);
            if (buffer_.size() < 1024 * 256) buffer_.resize(buffer_.size() * 2);
            ResetEvent(io_.hEvent);
            ReadFile(pipe_handle_, buffer_.data(), (DWORD)buffer_.size(), 0, &io_);
          }
          else {
            if (!reconnected && (err == ERROR_BROKEN_PIPE || err == ERROR_NO_DATA) && job_handle_.is_valid()) {
                connected_ = false;
                pipe_handle_.reset();
                Connect(job_handle_.get());
                Initialize();
                reconnected = true; goto retry;
            }
            response.set_err("read error");
            break;
          }
        }
      }
      else if (signaled == WAIT_TIMEOUT) {
        std::string err = "timeout waiting for ";
        err.append(language_descriptor_.name_);
        err.append(" response");
        response.set_err(err);
        break;
      }
      else {
        response.set_err("wait error");
        break;
      }
    }
  }
  SetEvent(callback_info_.default_signaled_event_);

  // ─── Diagnostic Stream: route Python piggybacked diagnostics ─────────
  // Python can't use the callback pipe (timing bug), so diagnostic output
  // is piggybacked on the function response via console_output fields.
  if (language_descriptor_.name_ == "Python") {
    if (!response.console_output().empty() || !response.console_error_output().empty()) {
      rj2xcl::DiagnosticRouter::Instance().RoutePythonDiagnostics(
          response.console_output(), response.console_error_output());
    }
  }
}

FUNCTION_LIST LanguageService::CreateFunctionList(const RJ2XCLBuffers::CallResponse &message, uint32_t key, const std::string &name, std::shared_ptr<LanguageService> language_service_pointer) {

  FUNCTION_LIST function_list;

  if (message.operation_case() == RJ2XCLBuffers::CallResponse::OperationCase::kErr) return function_list; // error: no functions
  else if (message.operation_case() == RJ2XCLBuffers::CallResponse::OperationCase::kFunctionList) {

    for (auto descriptor : message.function_list().functions()) {
      ARGUMENT_LIST arglist;
      for (auto argument : descriptor.arguments()) {
        std::stringstream value;
        auto default_value = argument.default_value();
        int value_case = default_value.value_case();
        switch (default_value.value_case()) {
        case RJ2XCLBuffers::Variable::ValueCase::kBoolean:
          value << (default_value.boolean() ? "TRUE" : "FALSE");
          break;
        case RJ2XCLBuffers::Variable::ValueCase::kReal:
          value << default_value.real();
          break;
        case RJ2XCLBuffers::Variable::ValueCase::kInteger:
          value << default_value.integer();
          break;
        case RJ2XCLBuffers::Variable::ValueCase::kStr:
          value << default_value.str();
          break;
        }
        arglist.push_back(std::make_shared<ArgumentDescriptor>(argument.name(), value.str(), argument.description()));
      }
      function_list.push_back(std::make_shared<FunctionDescriptor>(
        descriptor.function().name(), 
        descriptor.function().name(), 
        name, key, descriptor.category(), descriptor.function().description(), 
        arglist, descriptor.flags(), language_service_pointer));
    }
  }

  return function_list;

}

FUNCTION_LIST LanguageService::MapLanguageFunctions(uint32_t key, std::shared_ptr<LanguageService> language_service) {

  if (!connected_) return {};

  // Fix 4: Don't attempt pipe call on dead/broken processes
  if (health_status_ == HealthStatus::Unavailable) {
    RJ2XCL_LOG_WARN("Skipping MapLanguageFunctions for %s — service is Unavailable", name().c_str());
    return {};
  }

  RJ2XCLBuffers::CallResponse call;
  RJ2XCLBuffers::CallResponse response;

  call.mutable_function_call()->set_function("list-functions");
  call.mutable_function_call()->set_target(RJ2XCLBuffers::CallTarget::system);
  call.set_wait(true);

  Call(response, call);
  
  return LanguageService::CreateFunctionList(response, key, name(), language_service);

}

int LanguageService::StartChildProcess(HANDLE job_handle) {

  // cache
  std::string old_path = APIFunctions::GetPath();
  RJ2XCL_LOG_INFO("StartChildProcess for %s, prepend_path_='%s'", language_descriptor_.name_.c_str(), language_descriptor_.prepend_path_.c_str());

  std::string prepend = language_descriptor_.prepend_path_;
  InterpolateString(prepend);

  APIFunctions::PrependPath(prepend);
  RJ2XCL_LOG_INFO("PrependPath: %s", prepend.c_str());

  std::string arguments = language_descriptor_.command_arguments_; 
  InterpolateString(arguments);
  RJ2XCL_LOG_INFO("Arguments: %s", arguments.c_str());

  std::stringstream command;
  command << "\"" << child_path_ << "\" -p " << pipe_name_ << " " << arguments;

  // Use vector for automatic memory management
  std::string cmd_str = command.str();
  std::vector<char> args(cmd_str.begin(), cmd_str.end());
  args.push_back('\0');

  RJ2XCL_LOG_INFO("StartChildProcess: %s", args.data());

  int result = LaunchProcess(job_handle, args.data());
  if (result) {
    RJ2XCL_LOG_ERR("LaunchProcess FAILED: error=%d", result);
  }

  // restore
  APIFunctions::SetPath(old_path);

  return result;
}





