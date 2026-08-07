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

#include "controlr.h"
#include "windows_api_functions.h"
#include "result.h"
#include "json11\json11.hpp"
#include "child_process_log.h"
#include "IPC/MessageValidator.h"
#include <atomic>
#include <mutex>

// Forward declare log file for CHILD_LOG macros used in struct methods

/**
 * RControllerState — H4 (Work Plan V2): Thread-Safe Controller State
 *
 * Design rationale:
 *  - `pipes`, `handles`, `console_buffer`, `console_client`, `active_pipe`
 *    are accessed ONLY from InputStreamRead (R's main thread, never multi-threaded).
 *    No mutex is needed for these; they are encapsulated for clarity and correctness.
 *
 *  - `user_break_flag` IS written by ManagementThreadFunction (separate OS thread)
 *    and read by RTick/main thread. Uses std::atomic<bool> for lock-free safety.
 *
 *  - `language_tag` is set once in main() before threads start, safe as-is.
 */
struct RControllerState {
  // ─── R Main Thread Only ───────────────────────────────────────────────────
  std::vector<Pipe*> pipes;
  std::vector<HANDLE> handles;
  std::vector<std::string> console_buffer;
  std::stack<int> active_pipe;
  int console_client = -1;

  // ─── Cross-Thread (atomic, no mutex needed) ──────────────────────────────
  std::atomic<bool> user_break_flag { false };

  // ─── Read-Only after initialization ─────────────────────────────────────
  std::string language_tag;
  std::string pipename;
  std::string rhome;

  // ─── Helpers ─────────────────────────────────────────────────────────────
  bool has_console() const { return console_client >= 0; }

  void set_console_client(int index) {
    console_client = index;
    CHILD_LOG("set console client -> %d", index);
  }

  void clear_console_client() {
    console_client = -1;
  }

  void cleanup() {
    handles.clear();
    for (auto pipe : pipes) delete pipe;
    pipes.clear();
  }
};

// Single process-wide instance — owned by main(), accessed via pointer by callbacks
static RControllerState* g_state = nullptr;

// Convenience accessors  to avoid pervasive changes to function signatures
inline RControllerState& State() { return *g_state; }

// Legacy interface aliases (maintain ABI with controlr.h callbacks)
std::string& pipename_ref()        { return g_state->pipename; }
std::string& language_tag_ref()    { return g_state->language_tag; }


/** debug/util function */
std::string GetLastErrorAsString(DWORD err = -1)
{
  //Get the error message, if any.
  DWORD errorMessageID = err;
  if (-1 == err) errorMessageID = ::GetLastError();
  if (errorMessageID == 0)
    return std::string(); //No error message has been recorded

  LPSTR messageBuffer = nullptr;
  size_t size = FormatMessageA(FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM | FORMAT_MESSAGE_IGNORE_INSERTS,
    NULL, errorMessageID, MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT), (LPSTR)&messageBuffer, 0, NULL);

  std::string message(messageBuffer, size);

  //Free the buffer.
  LocalFree(messageBuffer);

  return message;
}

void DirectCallback(const char *channel, const char *data, bool buffered) {

}

/**
 * frame message and push to console client, or to queue if
 * no console client is connected
 */
void PushConsoleMessage(google::protobuf::Message &message) {

  std::string framed = MessageUtilities::Frame(message);
  if (State().has_console()) {
    State().pipes[State().console_client]->PushWrite(framed);
  }
  else {
    State().console_buffer.push_back(framed);
  }
}

void ConsoleResetPrompt(uint32_t id) {
  RJ2XCLBuffers::CallResponse message;
  message.set_id(id);
  message.mutable_function_call()->set_target(RJ2XCLBuffers::CallTarget::system);
  message.mutable_function_call()->set_function("reset-prompt");
  PushConsoleMessage(message);
}

void ConsoleControlMessage(const std::string &control_message) {
  RJ2XCLBuffers::CallResponse message;
  message.mutable_function_call()->set_target(RJ2XCLBuffers::CallTarget::system);
  message.mutable_function_call()->set_function(control_message);
  PushConsoleMessage(message);
}

void ConsolePrompt(const char *prompt, uint32_t id) {
  RJ2XCLBuffers::CallResponse message;
  message.set_id(id);
  message.mutable_console()->set_prompt(prompt);
  PushConsoleMessage(message);
}

void ConsoleMessage(const char *buf, int len, int flag) {
  RJ2XCLBuffers::CallResponse message;
  if (flag) message.mutable_console()->set_err(buf);
  else message.mutable_console()->set_text(buf);
  PushConsoleMessage(message);
}

bool ConsoleCallback(const RJ2XCLBuffers::CallResponse &call, RJ2XCLBuffers::CallResponse &response) {

  if (!State().has_console()) return false;
  Pipe *pipe = State().pipes[State().console_client];

  if (!pipe->connected()) return false;

  pipe->PushWrite(MessageUtilities::Frame(call));
  pipe->StartRead();

  while (pipe->writing()) {
    pipe->NextWrite();
    Sleep(1);
  }

  std::string data;
  DWORD result;
  do {
    result = pipe->Read(data, true);
  } 
  while (result == ERROR_MORE_DATA);

  if (!result) {
    if (!rj2xcl::ipc::MessageValidator::SafeUnframe(response, data.c_str(), (uint32_t)data.length())) {
      CHILD_LOG_ERR("SafeUnframe failed on callback response (len=%u)", (uint32_t)data.length());
    }
  }

  pipe->StartRead();
  return (result == 0);
}

bool Callback(const RJ2XCLBuffers::CallResponse &call, RJ2XCLBuffers::CallResponse &response) {

  // Always use the dedicated callback pipe, regardless of active_pipe
  Pipe *pipe = State().pipes[rj2xcl::Constants::kCallbackPipeIndex];

  if (!pipe->connected()) return false;

  pipe->PushWrite(MessageUtilities::Frame(call));
  pipe->StartRead();

  std::string data;
  DWORD result;
  do {
    result = pipe->Read(data, true);
  } while (result == ERROR_MORE_DATA);

  if (!result) {
    if (!rj2xcl::ipc::MessageValidator::SafeUnframe(response, data.c_str(), (uint32_t)data.length())) {
      CHILD_LOG_ERR("SafeUnframe failed on callback response (len=%u)", (uint32_t)data.length());
    }
  }
  
  pipe->StartRead();
  return (result == 0);
}

void Shutdown(int exit_code) {
  ExitProcess(0);
}

void NextPipeInstance(bool block, std::string &name) {
  Pipe *pipe = new Pipe;
  pipe->Start(name, block);
  State().handles.push_back(pipe->wait_handle_read());
  State().handles.push_back(pipe->wait_handle_write());
  State().pipes.push_back(pipe);
}

void CloseClient(int index) {

  if (index == rj2xcl::Constants::kPrimaryClientPipeIndex) Shutdown(-1);
  else if (index == rj2xcl::Constants::kCallbackPipeIndex) {
    CHILD_LOG_WARN("callback pipe closed");
  }
  else {
    State().pipes[index]->Reset();
    if (index == State().console_client) {
      State().clear_console_client();
    }
  }
}

void QueueConsoleWrites() {
  State().pipes[State().console_client]->QueueWrites(State().console_buffer);
  State().console_buffer.clear();
}

/**
 * in an effort to make the core language agnostic, all actual functions are moved
 * here. this should cover things like initialization and setting the COM pointers.
 *
 * the caller uses symbolic constants that call these functions in the appropriate
 * language.
 */
int SystemCall(RJ2XCLBuffers::CallResponse &response, const RJ2XCLBuffers::CallResponse &call, int pipe_index) {
  std::string function = call.function_call().function();

  RJ2XCLBuffers::CallResponse translated_call;
  translated_call.CopyFrom(call);

  if (!function.compare("install-application-pointer")) {
    translated_call.mutable_function_call()->set_target(RJ2XCLBuffers::CallTarget::language);
    translated_call.mutable_function_call()->set_function("RJ$install.application.pointer");
    RCall(response, translated_call);
  }
  else if (!function.compare("list-functions")) {
    response.set_id(call.id());
    ListScriptFunctions(response);
  }
  else if (!function.compare("get-language")) {
    response.mutable_result()->set_str(State().language_tag);
  }
  else if (!function.compare("read-source-file")) {
    std::string file = call.function_call().arguments(0).str();
    bool notify = false;
    if (call.function_call().arguments_size() > 1) notify = call.function_call().arguments(1).boolean();
    bool success = false;
    if( file.length()){
      success = ReadSourceFile(file, notify);
    }
    response.mutable_result()->set_boolean(success);
  }
  else if (!function.compare("shutdown")) {
    ConsoleControlMessage("shutdown");
    // Shutdown(0);
    return SYSTEMCALL_SHUTDOWN;
  }
  else if (!function.compare("console")) {
    if (!State().has_console()) {
      State().set_console_client(pipe_index);
      QueueConsoleWrites();
    }
    else CHILD_LOG_WARN("console client already set");
  }
  else if (!function.compare("close")) {
    CloseClient(pipe_index);
    return SYSTEMCALL_OK; //  break; // no response?
  }
  else {
    CHILD_LOG("ENOTIMPL (system): %s", function.c_str());
    response.mutable_result()->set_boolean(false);
  }

  return SYSTEMCALL_OK;

}

int InputStreamRead(const char *prompt, unsigned char *buf, int len, int addtohistory, bool is_continuation) {

  // it turns out this function can get called recursively. we
  // hijack this function to run non-interactive R calls, but if
  // one of those calls wants a shell interface (such as a debug
  // browser, it will call into this function again). this gets
  // a little hard to track on the UI side, as we have extra prompts
  // from the internal calls, but we don't know when those are 
  // finished.

  // however we should be able to figure this out just by tracking
  // recursion. note that this is never threaded.

  static uint32_t call_depth = 0;
  static bool recursive_calls = false;

  static uint32_t prompt_transaction_id = 0;

  std::string buffer;
  std::string message;

  DWORD result;

  if (call_depth > 0) {
    // set flag to indicate we'll need to "unwind" the console
    CHILD_LOG("console prompt at depth %d", call_depth);
    recursive_calls = true;
  }

  ConsolePrompt(prompt, prompt_transaction_id);

  while (true) {

    result = WaitForMultipleObjects((DWORD)State().handles.size(), &(State().handles[0]), FALSE, 100);

    if (result >= WAIT_OBJECT_0 && result - WAIT_OBJECT_0 < 16) {

      int offset = (result - WAIT_OBJECT_0);
      int index = offset / 2;
      bool write = offset % 2;
      auto pipe = State().pipes[index];

      if (!index) CHILD_LOG("pipe event on index 0 (%s)", write ? "write" : "read");

      ResetEvent(State().handles[result - WAIT_OBJECT_0]);

      if (!pipe->connected()) {
        CHILD_LOG("connect (%d)", index);
        pipe->Connect(); // this will start reading
        if (State().pipes.size() < rj2xcl::Constants::kMaxPipeCount) NextPipeInstance(false, State().pipename);
      }
      else if (write) {
        pipe->NextWrite();
      }
      else {
        result = pipe->Read(message);

        if (!result) {

          RJ2XCLBuffers::CallResponse call, response;
          bool success = rj2xcl::ipc::MessageValidator::SafeUnframe(call, message.c_str(), (uint32_t)message.length());

          if (success) {

            CHILD_LOG("Received message on pipe %d, op=%d, wait=%d", index, call.operation_case(), call.wait());

            response.set_id(call.id());
            switch (call.operation_case()) {

            case RJ2XCLBuffers::CallResponse::kFunctionCall:
              call_depth++;
              State().active_pipe.push(index);
              switch (call.function_call().target()) {
              case RJ2XCLBuffers::CallTarget::system:
                if (SYSTEMCALL_SHUTDOWN == SystemCall(response, call, index)) {
                  Shutdown(0); // we're not handling this well
                  return 0; // will terminate R loop
                }
                break;
              default:
                RCall(response, call);
                break;
              }
              State().active_pipe.pop();
              call_depth--;
              if (call.wait()) pipe->PushWrite(MessageUtilities::Frame(response));
              break;

            case RJ2XCLBuffers::CallResponse::kUserCommand:
              ExecUserCommand(response, call);
              if (call.wait()) pipe->PushWrite(MessageUtilities::Frame(response));
              break;

            case RJ2XCLBuffers::CallResponse::kCode:
              call_depth++;
              State().active_pipe.push(index);
              RExec(response, call);
              State().active_pipe.pop();
              call_depth--;
              if (call.wait()) pipe->PushWrite(MessageUtilities::Frame(response));
              break;

            case RJ2XCLBuffers::CallResponse::kShellCommand:
              len = min(len - 2, (int)call.shell_command().length());
              strcpy_s((char*)buf, len + 1, call.shell_command().c_str());
              buf[len++] = '\n';
              buf[len++] = 0;
              prompt_transaction_id = call.id();
              pipe->StartRead();

              // start read and then exit this function; that will cycle the R REPL loop.
              // the (implicit/explicit) response from this command is going to be the next 
              // prompt.

              return len;

            default:
              // ...
              0;
            }

            if (call_depth == 0 && recursive_calls) {
              CHILD_LOG("unwind recursive prompt stack");
              recursive_calls = false;
              ConsoleResetPrompt(prompt_transaction_id);
            }

          }
          else {
            if (pipe->error()) {
              CHILD_LOG_ERR("ERR in system pipe: %d", result);
            }
            else CHILD_LOG_ERR("error parsing packet: %d", result);
          }
          if (pipe->connected() && !pipe->reading()) {
            pipe->StartRead();
          }
        }
        else {
          if (result == ERROR_BROKEN_PIPE) {
            CHILD_LOG_ERR("broken pipe (%d)", index);
            CloseClient(index);
          }
        }
      }
    }
    else if (result == WAIT_TIMEOUT) {
      RTick();
      UpdateSpreadsheetGraphics();
    }
    else {
      CHILD_LOG_ERR("ERR %d: %s", result, GetLastErrorAsString(result).c_str());
      break;
    }
  }

  return 0;
}

unsigned __stdcall ManagementThreadFunction(void *data) {

  DWORD result;
  Pipe pipe;
  char *name = reinterpret_cast<char*>(data);

  CHILD_LOG("start management pipe on %s", name);

  int rslt = pipe.Start(name, false);
  std::string message;

  while (true) {
    result = WaitForSingleObject(pipe.wait_handle_read(), 1000);
    if (result == WAIT_OBJECT_0) {
      ResetEvent(pipe.wait_handle_read());
      if (!pipe.connected()) {
        CHILD_LOG("connect management pipe");
        pipe.Connect(); // this will start reading
      }
      else {
        result = pipe.Read(message);
        if (!result) {
          RJ2XCLBuffers::CallResponse call;
          bool success = rj2xcl::ipc::MessageValidator::SafeUnframe(call, message.c_str(), (uint32_t)message.length());
          if (success) {
            //std::string command = call.control_message();
            std::string command = call.function_call().function();
            if (command.length()) {
              if (!command.compare("break")) {
                State().user_break_flag = true;
                RSetUserBreak();
              }
              else {
                CHILD_LOG_WARN("unexpected system command (management pipe): %s", command.c_str());
              }
            }
          }
          else {
            CHILD_LOG_ERR("error parsing management message");
          }
          pipe.StartRead();
        }
        else {
          if (result == ERROR_BROKEN_PIPE) {
            CHILD_LOG_ERR("broken pipe in management thread");
            pipe.Reset();
          }
        }
      }
    }
    else if (result != WAIT_TIMEOUT) {
      CHILD_LOG_ERR("error in management thread: %d", GetLastError());
      pipe.Reset();
      break;
    }
  }
  return 0;
}

void ScrubPath(char *string) {

  int len = strlen(string);
  for (int i = 0; i < len; ) {
    if (i > 1 && string[i] == '\\' && string[i - 1] == '\\') {
      CHILD_LOG_DEBUG("ScrubPath mark @ %d", i);
      for (int j = i; j < len; j++) {
        string[j] = string[j+1]; // also moves up trailing null
      }
      len--;
    }
    else i++;
  }

}

int main(int argc, char** argv) {

  // H4: Create RControllerState instance — owns all shared state for this process
  RControllerState state;
  g_state = &state;

  // Open log file for ControlR diagnostics
  rj2xcl::ChildProcessLog::Initialize("controlr");
  CHILD_LOG("ControlR starting...");

  char buffer[MAX_PATH];
  int major, minor, patch;
  RGetVersion(&major, &minor, &patch);

  CHILD_LOG("R version: %d.%d.%d", major, minor, patch);

  // Read version constraints from config (H1: Support R 4.x+)
  int min_major = 3, min_minor = 5, max_major = 99;
  GetEnvironmentVariableA("RJ2XCL_HOME", buffer, MAX_PATH);
  {
    std::string config_path(buffer);
    config_path.append("rj2xcl-config.json");
    auto config_result = APIFunctions::FileContents(config_path);
    if (config_result.is_success()) {
      std::string parse_error;
      auto config = json11::Json::parse(config_result.value(), parse_error, json11::COMMENTS);
      if (parse_error.empty()) {
        auto r_config = config["NEVEN"]["R"];
        if (r_config["minMajor"].is_number()) min_major = r_config["minMajor"].int_value();
        if (r_config["minMinor"].is_number()) min_minor = r_config["minMinor"].int_value();
        if (r_config["maxMajor"].is_number()) max_major = r_config["maxMajor"].int_value();
      }
    }
  }

  bool version_ok = (major > min_major) ||
                    (major == min_major && minor >= min_minor);
  bool version_within_max = (major <= max_major);

  if (!version_ok || !version_within_max) {
    CHILD_LOG_ERR("R version %d.%d not supported. Requires >= %d.%d and <= %d.x",
        major, minor, min_major, min_minor, max_major);
    rj2xcl::ChildProcessLog::Shutdown();
    return PROCESS_ERROR_UNSUPPORTED_VERSION;
  }

  std::stringstream ss;
  ss << "R::" << major << "." << minor << "." << patch;
  State().language_tag = ss.str();

  for (int i = 0; i < argc; i++) {
    if (!strncmp(argv[i], "-p", 2) && i < argc - 1) {
      State().pipename = argv[++i];
    }
    else if (!strncmp(argv[i], "-r", 2) && i < argc - 1) {
      State().rhome = argv[++i];
    }
  }

  if (!State().pipename.length()) {
    CHILD_LOG_ERR("call with -p pipename");
    return PROCESS_ERROR_CONFIGURATION_ERROR;
  }
  if (!State().rhome.length()) {
    CHILD_LOG_ERR("call with -r rhome");
    return PROCESS_ERROR_CONFIGURATION_ERROR;
  }

  CHILD_LOG("pipe: %s", State().pipename.c_str());
  CHILD_LOG("pid: %d", _getpid());

  // set R_LIBS from config file, if there's a lib field

  GetEnvironmentVariableA("RJ2XCL_HOME", buffer, MAX_PATH);
  std::string config_data;
  std::string config_path(buffer);
  config_path.append("rj2xcl-config.json");
  auto config_result = APIFunctions::FileContents(config_path);
  if (config_result.is_success()) {
    config_data = config_result.value();
    std::string err;
    json11::Json config = json11::Json::parse(config_data, err, json11::COMMENTS);
    json11::Json lib_dir = config["NEVEN"]["R"]["lib"];

    if (lib_dir.is_string()) {
      ExpandEnvironmentStringsA(lib_dir.string_value().c_str(), buffer, MAX_PATH);
      CHILD_LOG("set R_LIBS from config file: %s", buffer);
      SetEnvironmentVariableA("R_LIBS", buffer);
    }
  }

  // we need a non-const block for the thread function. 
  // it just gets used once, and immediately

  sprintf_s(buffer, "%s-M", State().pipename.c_str());
  uintptr_t thread_handle = _beginthreadex(0, 0, ManagementThreadFunction, buffer, 0, 0);

  std::string callback_pipe_name = State().pipename;
  callback_pipe_name += "-CB";
  NextPipeInstance(false, callback_pipe_name);

  NextPipeInstance(true, State().pipename);
  NextPipeInstance(false, State().pipename);

  char* args[] = { argv[0], "--no-save", "--no-restore", "--encoding=UTF-8" };

  CHILD_LOG("Starting RLoop with rhome=%s", State().rhome.c_str());
  CHILD_LOG("About to call RLoop...");
  rj2xcl::ChildProcessLog::Shutdown();

  // Reopen after RLoop returns
  int result = RLoop(State().rhome.c_str(), "", 4, args);
  
  rj2xcl::ChildProcessLog::Initialize("controlr");
  CHILD_LOG("RLoop returned: %d", result);
  if (result) CHILD_LOG_ERR("R loop failed: %d", result);

  state.cleanup();

  CHILD_LOG("ControlR exiting normally");
  rj2xcl::ChildProcessLog::Shutdown();
  return 0;
}
