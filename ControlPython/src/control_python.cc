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

#include "control_python.h"
#include "python_interface.h"
#include "child_process_log.h"
#include "Constants.h"
#include "IPC/MessageValidator.h"

#include <Python.h>

std::string language_tag;

// Handle for signaling break (ctrl+c); set as first handle in pipe loop set
HANDLE break_event_handle = CreateEvent(0, TRUE, FALSE, 0);
std::vector<HANDLE> handles = { break_event_handle };

std::vector<Pipe*> pipes;
std::vector<std::string> console_buffer;

std::string pipename;
int console_client = -1;

Pipe stdout_pipe, stderr_pipe;


void NextPipeInstance(bool block, std::string &name) {
  Pipe *pipe = new Pipe;
  int rslt = pipe->Start(name, block);
  handles.push_back(pipe->wait_handle_read());
  handles.push_back(pipe->wait_handle_write());
  pipes.push_back(pipe);
}

void CloseClient(int index) {
  pipes[index]->Reset();
  if (index == console_client) {
    console_client = -1;
  }
}

std::string GetLastErrorAsString(DWORD err = -1) {
  DWORD errorMessageID = err;
  if (-1 == err) errorMessageID = ::GetLastError();
  if (errorMessageID == 0)
    return std::string();

  LPSTR messageBuffer = nullptr;
  size_t size = FormatMessageA(FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM | FORMAT_MESSAGE_IGNORE_INSERTS,
    NULL, errorMessageID, MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT), (LPSTR)&messageBuffer, 0, NULL);

  std::string message(messageBuffer, size);
  LocalFree(messageBuffer);
  return message;
}


/**
 * Frame message and push to console client, or to queue if
 * no console client is connected.
 */
void PushConsoleMessage(google::protobuf::Message &message) {
  std::string framed = MessageUtilities::Frame(message);
  if (console_client >= 0) {
    pipes[console_client]->PushWrite(framed);
  }
  else {
    console_buffer.push_back(framed);
  }
}

void PushConsoleString(const std::string &str) {
  if (console_client >= 0) {
    pipes[console_client]->PushWrite(str);
  }
  else {
    console_buffer.push_back(str);
  }
}

void ConsolePrompt(const char *prompt, uint32_t id) {
  RJ2XCLBuffers::CallResponse message;
  message.set_id(id);
  message.mutable_console()->set_prompt(prompt);
  PushConsoleMessage(message);
}

void QueueConsoleWrites() {
  pipes[console_client]->QueueWrites(console_buffer);
  console_buffer.clear();
}


/**
 * System call dispatcher — handles internal commands from the XLL.
 */
bool SystemCall(RJ2XCLBuffers::CallResponse &response, const RJ2XCLBuffers::CallResponse &call, int pipe_index) {
  std::string function = call.function_call().function();

  if (!function.compare("get-language")) {
    response.mutable_result()->set_str(language_tag);
  }
  else if (!function.compare("read-source-file")) {
    std::string file = call.function_call().arguments(0).str();
    bool notify = false;
    if (call.function_call().arguments_size() > 1) notify = call.function_call().arguments(1).boolean();
    bool success = false;
    if (file.length()) {
      CHILD_LOG("read source: %s", file.c_str());
      success = ReadSourceFile(file, notify);
    }
    response.mutable_result()->set_boolean(success);
  }
  else if (!function.compare("list-functions")) {
    ListScriptFunctions(response, call);
  }
  else if (!function.compare("shutdown")) {
    // Graceful shutdown
  }
  else if (!function.compare("console")) {
    if (console_client < 0) {
      console_client = pipe_index;
      CHILD_LOG("set console client -> %d", pipe_index);
      QueueConsoleWrites();
    }
  }
  else if (!function.compare("close")) {
    CloseClient(pipe_index);
    return false;
  }
  else {
    CHILD_LOG("ENOTIMPL (system): %s", function.c_str());
    response.mutable_result()->set_boolean(false);
  }

  return true;
}

std::string shell_buffer;

/**
 * Main pipe loop — reads Protobuf messages and dispatches to handlers.
 */
void pipe_loop() {

  char default_prompt[] = ">>> ";
  char continuation_prompt[] = "... ";

  DWORD result;
  uint32_t console_prompt_id = 1;
  std::string message;

  ConsolePrompt(default_prompt, console_prompt_id++);

  while (true) {

    result = WaitForMultipleObjects((DWORD)handles.size(), &(handles[0]), FALSE, 100);

    if (result == WAIT_OBJECT_0) {
      // Break handle
      CHILD_LOG("break handle set");
      ::ResetEvent(break_event_handle);
      shell_buffer.clear();
      ConsolePrompt(default_prompt, console_prompt_id++);
    }
    else if (result >= WAIT_OBJECT_0 && result - WAIT_OBJECT_0 < 16) {

      int offset = (result - WAIT_OBJECT_0 - 1); // -1 for break handle at top
      int index = offset / 2;
      bool write = offset % 2;
      auto pipe = pipes[index];

      ResetEvent(handles[result - WAIT_OBJECT_0]);

      if (!pipe->connected()) {
        CHILD_LOG("connect (%d)", index);
        pipe->Connect();
        if (pipes.size() < rj2xcl::Constants::kMaxPipeCount) NextPipeInstance(false, pipename);
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

            response.set_id(call.id());

            switch (call.operation_case()) {

            case RJ2XCLBuffers::CallResponse::kFunctionCall:
              switch (call.function_call().target()) {
              case RJ2XCLBuffers::CallTarget::system:
                SystemCall(response, call, index);
                break;
              default:
                PythonCall(response, call);
                break;
              }
              if (call.wait()) pipe->PushWrite(MessageUtilities::Frame(response));
              break;

            case RJ2XCLBuffers::CallResponse::kCode:
              PythonExec(response, call);
              if (call.wait()) pipe->PushWrite(MessageUtilities::Frame(response));
              break;

            case RJ2XCLBuffers::CallResponse::kShellCommand:
            {
              int exec_result = PythonShellExec(call.shell_command(), shell_buffer);
              console_prompt_id = call.id();
              if (exec_result == 1) {
                // Incomplete — multi-line input
                shell_buffer += call.shell_command();
                shell_buffer += "\n";
                ConsolePrompt(continuation_prompt, console_prompt_id);
              }
              else {
                shell_buffer.clear();
                ConsolePrompt(default_prompt, console_prompt_id);
              }
              break;
            }

            default:
              break;
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
      // Idle — could run Python event loop here if needed
    }
    else {
      CHILD_LOG_ERR("ERR %d: %s", result, GetLastErrorAsString(result).c_str());
      break;
    }
  }
}

void TruncateBuffer(std::string &buffer, uint32_t target_length = 1024 * 8) {
  if (buffer.length() > (target_length + 1024)) {
    buffer.erase(0, buffer.length() - target_length);
  }
}

unsigned __stdcall StdioThreadFunction(void *data) {

  Pipe **stdio_pipes = (Pipe**)data;
  std::string str;

  std::string stdout_buffer;
  std::string stderr_buffer;

  HANDLE wait_handles[] = { stdio_pipes[0]->wait_handle_read(), stdio_pipes[1]->wait_handle_read(), stdout_pipe.wait_handle_read(), stderr_pipe.wait_handle_read() };
  while (true) {
    DWORD wait_result = WaitForMultipleObjects(4, wait_handles, FALSE, 1000);
    int index = wait_result - WAIT_OBJECT_0;

    if (index == 2) {
      ResetEvent(stdout_pipe.wait_handle_read());
      if (!stdout_pipe.connected()) {
        stdout_pipe.Connect();
        if (stdout_buffer.length()) stdout_pipe.PushWrite(stdout_buffer);
        stdout_buffer.clear();
      }
      else {
        int result = stdout_pipe.Read(str, false);
        if (stdout_pipe.error()) stdout_pipe.Reset();
      }
    }
    else if (index == 3) {
      ResetEvent(stderr_pipe.wait_handle_read());
      if (!stderr_pipe.connected()) {
        stderr_pipe.Connect();
        if (stderr_buffer.length()) stderr_pipe.PushWrite(stderr_buffer);
        stderr_buffer.clear();
      }
      else {
        int result = stderr_pipe.Read(str, false);
        if (stderr_pipe.error()) stderr_pipe.Reset();
      }
    }
    else if (index >= 0 && index < 2) {
      ResetEvent(stdio_pipes[index]->wait_handle_read());
      if (!stdio_pipes[index]->connected()) {
        stdio_pipes[index]->Connect(true);
        CHILD_LOG("connect stdio pipe %d", index);
      }
      else {
        DWORD read_result = stdio_pipes[index]->Read(str, false);
        stdio_pipes[index]->StartRead();

        if (index) {
          if (stderr_pipe.connected()) {
            stderr_pipe.PushWrite(str);
          }
          else {
            TruncateBuffer(stderr_buffer.append(str));
          }
        }
        else {
          if (stdout_pipe.connected()) {
            stdout_pipe.PushWrite(str);
          }
          else {
            TruncateBuffer(stdout_buffer.append(str));
          }
        }
      }
    }
    else if (wait_result == WAIT_TIMEOUT) {
      // Idle
    }
    else {
      CHILD_LOG_ERR("ERR in stdio wait: %d", GetLastError());
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
        pipe.Connect();
      }
      else {
        result = pipe.Read(message);
        if (!result) {
          RJ2XCLBuffers::CallResponse call;
          bool success = rj2xcl::ipc::MessageValidator::SafeUnframe(call, message.c_str(), (uint32_t)message.length());
          if (success) {
            std::string command = call.function_call().function();
            if (command.length()) {
              if (!command.compare("break")) {
                // Signal break to Python (KeyboardInterrupt)
                ::SetEvent(break_event_handle);
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


bool Callback(const RJ2XCLBuffers::CallResponse &call, RJ2XCLBuffers::CallResponse &response) {

  Pipe *pipe = pipes[rj2xcl::Constants::kCallbackPipeIndex];

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


/**
 * SEH-guarded Python initialization.
 * Separated from main() because __try/__except cannot coexist with
 * C++ objects that have destructors in the same function (MSVC C2712).
 *
 * @return 0 on success, PROCESS_ERROR_CONFIGURATION_ERROR on SEH exception.
 */
static int InitializePythonWithSEH() {
  __try {
    Py_Initialize();
  }
  __except(EXCEPTION_EXECUTE_HANDLER) {
    CHILD_LOG_ERR("FATAL: Py_Initialize() raised exception 0x%08X (possible STATUS_STACK_BUFFER_OVERRUN)",
                  GetExceptionCode());
    return PROCESS_ERROR_CONFIGURATION_ERROR;
  }
  return 0;
}


int main(int argc, char **argv) {

  rj2xcl::ChildProcessLog::Initialize("controlpython");
  CHILD_LOG("ControlPython starting...");

  // --- Parse command-line arguments ---
  std::string management_pipename;

  for (int i = 0; i < argc; i++) {
    if (!strncmp(argv[i], "-p", 2) && i < argc - 1) {
      pipename = argv[++i];
    }
    else if (!strncmp(argv[i], "-m", 2) && i < argc - 1) {
      management_pipename = argv[++i];
    }
  }

  if (!pipename.length()) {
    CHILD_LOG_ERR("call with -p pipename");
    rj2xcl::ChildProcessLog::Shutdown();
    return PROCESS_ERROR_CONFIGURATION_ERROR;
  }

  CHILD_LOG("pipe: %s", pipename.c_str());

  // --- Read config path ---
  char buffer[MAX_PATH];
  GetEnvironmentVariableA("RJ2XCL_HOME", buffer, MAX_PATH);
  std::string config_path(buffer);

  // --- Start management thread ---
  char mgmt_buffer[MAX_PATH];
  if (management_pipename.length()) {
    sprintf_s(mgmt_buffer, "%s", management_pipename.c_str());
  }
  else {
    sprintf_s(mgmt_buffer, "%s-M", pipename.c_str());
  }
  uintptr_t management_thread_handle = _beginthreadex(0, 0, ManagementThreadFunction, mgmt_buffer, 0, 0);

  // --- Setup stdio capture ---
  fflush(stdout);
  int console_stdout_fd = _dup(1);
  std::ofstream console_out(_fdopen(console_stdout_fd, "w"));
  std::cout.rdbuf(console_out.rdbuf());

  fflush(stderr);
  int console_stderr_fd = _dup(2);
  std::ofstream console_err(_fdopen(console_stderr_fd, "w"));
  std::cerr.rdbuf(console_err.rdbuf());

  {
    char buf2[MAX_PATH];
    sprintf_s(buf2, "%s-STDOUT", pipename.c_str());
    stdout_pipe.Start(buf2, false);

    sprintf_s(buf2, "%s-STDERR", pipename.c_str());
    stderr_pipe.Start(buf2, false);
  }

  Pipe *stdio_pipes[] = { new Pipe, new Pipe };

  stdio_pipes[0]->Start("stdout", false);
  HANDLE stdout_write_handle = CreateFileA(stdio_pipes[0]->full_name().c_str(), FILE_ALL_ACCESS, FILE_SHARE_READ | FILE_SHARE_WRITE, 0, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, 0);

  stdio_pipes[1]->Start("stderr", false);
  HANDLE stderr_write_handle = CreateFileA(stdio_pipes[1]->full_name().c_str(), FILE_ALL_ACCESS, FILE_SHARE_READ | FILE_SHARE_WRITE, 0, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, 0);

  _dup2(_open_osfhandle((intptr_t)stdout_write_handle, 0), 1);
  _dup2(_open_osfhandle((intptr_t)stderr_write_handle, 0), 2);

  uintptr_t io_thread_handle = _beginthreadex(0, 0, StdioThreadFunction, stdio_pipes, 0, 0);

  // --- Setup pipes ---
  // Start the callback pipe first (doesn't block)
  std::string callback_pipe_name = pipename;
  callback_pipe_name += "-CB";
  NextPipeInstance(false, callback_pipe_name);

  // Block on first client connection
  NextPipeInstance(true, pipename);

  CHILD_LOG("first pipe connected");

  // --- Initialize Python (AFTER pipe setup to reduce stack pressure) ---
  // SEH guard around Py_Initialize() to catch STATUS_STACK_BUFFER_OVERRUN.
  // Must be in a separate function because __try cannot coexist with C++ objects
  // that have destructors in the same function scope (MSVC limitation).
  int py_init_result = InitializePythonWithSEH();
  if (py_init_result != 0) {
    rj2xcl::ChildProcessLog::Shutdown();
    return py_init_result;
  }

  CHILD_LOG("Py_Initialize() succeeded");

  // Build language tag
  language_tag = "Python::";
  language_tag += std::to_string(PY_MAJOR_VERSION);
  language_tag += ".";
  language_tag += std::to_string(PY_MINOR_VERSION);
  language_tag += ".";
  language_tag += std::to_string(PY_MICRO_VERSION);
  CHILD_LOG("Python version: %s", language_tag.c_str());

  // --- Execute startup.py (with retry logic) ---
  PythonInit(config_path);

  // Check startup success — log warning but continue into pipe_loop
  if (!PythonStartupSucceeded()) {
    CHILD_LOG_WARN("startup.py failed — Python functions will not be available");
  }

  // --- Enter main pipe loop ---
  pipe_loop();

  // --- Cleanup ---
  Py_Finalize();

  handles.clear();
  for (auto pipe : pipes) delete pipe;
  pipes.clear();

  CHILD_LOG("ControlPython exiting normally");
  rj2xcl::ChildProcessLog::Shutdown();
  return 0;
}
