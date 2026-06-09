/**
 * Copyright (c) 2026 NEVEN Project
 * 
 * This file is part of NEVEN.
 *
 * NEVEN is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * NEVEN is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with NEVEN.  If not, see <http://www.gnu.org/licenses/>.
 */

#include "stdafx.h"
#include <cstdint>
#include <iostream>
#include "variable.pb.h"
#include "XLCALL.h"
#include "function_descriptor.h"
#include "LanguageManager.h"
#include "rj2xcl.h"
#include "rj2xcl_graphics.h"
#include "basic_functions.h"
#include "type_conversions.h"
#include "string_utilities.h"
#include "windows_api_functions.h"
#include "module_functions.h"
#include "message_utilities.h"
#include "..\resource.h"

#include "excel_com_type_libraries.h"
#include "excel_api_functions.h"

#include "rj2xcl_version.h"
#include "WinExcelBridge.h"
#include "GraphicsHandler.h"
#include "COMHandler.h"
#include "RaiiXlOper.h"
#include "rj2xcl_integration_constants.h"
#include "EnvService.h"
#include "QuartoService.h"
#include "ViewerManager.h"
#include "PlutoManager.h"
#include "MenuService.h"
#include "REPLLanguageAccessor.h"

namespace rj2xcl {
    void RegisterREPLLanguageAccessor();
}
#include "CrashHandler.h"
#include "NevenInitOrchestrator.h"
#include <TlHelp32.h>

RJ2XCL_Engine* RJ2XCL_Engine::instance_ = 0;

RJ2XCL_Engine *RJ2XCL_Engine::Instance()
{
	static RJ2XCL_Engine instance;
	return &instance;
}

void RJ2XCL_Engine::ResetForTesting() {
    rj2xcl::LanguageManager::Instance().ResetForTesting();
    function_list_.clear();
}

typedef int (PASCAL* MDCALLBACK12PROC)(int xlfn, int coper, LPXLOPER12 *rgpxloper12, LPXLOPER12 xloper12Res);
extern "C" void SetExcel12EntryPt(MDCALLBACK12PROC pMdCallBack12);

static LPXLOPER12 TempInt12(int i) {
  static XLOPER12 x;
  x.xltype = xltypeInt;
  x.val.w = i;
  return &x;
}

// ReadConfigFile removed, use ConfigService::Instance().ReadJsonFile

  

int RJ2XCL_Engine::UpdateFunctions() {

  RJ2XCL_LOG_INFO("Updating NEVEN functions...");
  UnregisterFunctions();

  // scrub
  function_list_.clear();

  // now update
  MapFunctions();
  RegisterFunctions();

  return 0;

}

RJ2XCL_Engine::RJ2XCL_Engine()
  : stream_pointer_(0)
  , ribbon_service_(new rj2xcl::RibbonService())
  , file_watch_service_(new rj2xcl::FileWatchService())
  , excel_bridge_(new rj2xcl::WinExcelBridge())
  , callback_dispatcher_(new rj2xcl::CallbackDispatcher())
{
}


void RJ2XCL_Engine::HideConsole() {
  rj2xcl::WindowManager::Instance().HideConsole();
}

void RJ2XCL_Engine::ShowConsole() {
  rj2xcl::WindowManager::Instance().ShowConsole();
}

void RJ2XCL_Engine::SetPointers(ULONG_PTR excel_pointer, ULONG_PTR ribbon_pointer) {

  ribbon_service_->SetRibbonPointer(reinterpret_cast<LPDISPATCH>(ribbon_pointer));

  application_dispatch_ = reinterpret_cast<LPDISPATCH>(excel_pointer);

  // marshall pointer
  AtlMarshalPtrInProc(application_dispatch_, IID_IDispatch, &stream_pointer_);

  // set pointer in various language services (only if connected)
  for (auto language_service : rj2xcl::LanguageManager::Instance().GetServices()) {
    if (language_service->connected()) {
      language_service->SetApplicationPointer(application_dispatch_);
    }
  }

}

void RJ2XCL_Engine::ShutdownConsole() {
  rj2xcl::WindowManager::Instance().ShutdownConsole();
}

void RJ2XCL_Engine::HandleCallback(const std::string &language) {

  DWORD wait_result = WaitForSingleObject(callback_info_.default_signaled_event_, 0);
  if (wait_result == WAIT_OBJECT_0) {

    RJ2XCLBuffers::CallResponse &call = callback_info_.callback_call_;
    RJ2XCLBuffers::CallResponse &response = callback_info_.callback_response_;

    if (stream_pointer_) {
      LPDISPATCH dispatch_pointer = nullptr;
      HRESULT hresult = AtlUnmarshalPtr(stream_pointer_, IID_IDispatch, (LPUNKNOWN*)&dispatch_pointer);

      if (SUCCEEDED(hresult) && dispatch_pointer) {
        CComQIPtr<Excel::_Application> application(dispatch_pointer);
        if (application) {
          CComVariant variant_macro = rj2xcl::constants::kContextSwitchMacro;
          CComBSTR language_bstr(language.c_str());
          CComVariant variant_argument = language_bstr;
          try {
            CComVariant variant_result = application->Run(variant_macro, variant_argument);
          } catch (...) {
            RJ2XCL_LOG_ERR("Exception in COM callback Run()");
            response.set_err("COM callback exception");
          }
        }
        else {
          RJ2XCL_LOG_ERR("QI for _Application failed");
          response.set_err("qi failed");
        }
        dispatch_pointer->Release();
        dispatch_pointer = nullptr;
      }
      else {
        RJ2XCL_LOG_ERR("AtlUnmarshalPtr failed: 0x%08X", hresult);
        response.set_err("unmarshal failed");
        // Do NOT Release if unmarshal failed — pointer is invalid
      }
    }
    else {
      response.set_err("invalid stream pointer");
    }

  }
  else {
    RJ2XCL_LOG_DEBUG("event 2 is not signaled; this is a spreadsheet function");
    RJ2XCL_LOG_DEBUG("callback waiting for signal");

    // let main thread handle
    SetEvent(callback_info_.default_unsignaled_event_);
    WaitForSingleObject(callback_info_.default_signaled_event_, INFINITE);
    RJ2XCL_LOG_DEBUG("callback signaled");
  }
}

int RJ2XCL_Engine::HandleCallbackOnThread(const std::string &language, const RJ2XCLBuffers::CallResponse *call, RJ2XCLBuffers::CallResponse *response) {

  if (!call) call = &(callback_info_.callback_call_);
  if (!response) response = &(callback_info_.callback_response_);

  int return_value = 0;

  response->set_id(call->id());

  if (call->operation_case() == RJ2XCLBuffers::CallResponse::OperationCase::kFunctionCall) {

    auto callback = call->function_call();
    if (callback.target() == RJ2XCLBuffers::CallTarget::language) {

      auto function = callback.function();
      if (!function.compare("excel")) {
        return_value = ExcelCallback(*call, *response);
      }
      else if (!function.compare("clear-user-buttons")) {
        ClearUserButtons();
        return_value = 0;
      }
      else if (function == "add-user-button") {
        return_value = ribbon_service_->AddUserButton(*call, *response, language);
      }
      else if (!function.compare("release-pointer")) {
        if (callback.arguments_size() > 0) {
          uint64_t pointer = callback.arguments(0).com_pointer().pointer();
          RJ2XCL_LOG_DEBUG("release pointer 0x%lx", pointer);
          object_map_.RemoveCOMPointer(static_cast<ULONG_PTR>(pointer));
        }
      }
      else {
        response->mutable_result()->set_boolean(false);
      }
    }
    else if (callback.target() == RJ2XCLBuffers::CallTarget::COM) {
      auto result = Dispatcher()->Dispatch("COM", language, *call, *response);
      return_value = result.is_success() ? 0 : result.error();
    }
    else if (callback.target() == RJ2XCLBuffers::CallTarget::graphics) {
      auto result = Dispatcher()->Dispatch("graphics", language, *call, *response);
      return_value = result.is_success() ? 0 : result.error();
    }
    else {
      response->mutable_result()->set_boolean(false);
    }
  }
  else if (call->operation_case() == RJ2XCLBuffers::CallResponse::OperationCase::kFunctionList) {

    if (language.length()) {

      std::shared_ptr<LanguageService> language_service = 0;

      uint32_t key = 0;
      auto services = rj2xcl::LanguageManager::Instance().GetServices();
      for (; key < services.size(); key++) {
        if (services[key]->name() == language) {
          language_service = services[key];
          break;
        }
      }
      if (key < services.size()) {

        UnregisterFunctions(); 

        FUNCTION_LIST temporary_list = LanguageService::CreateFunctionList(*call, key, language, language_service);
        for (auto function_pointer : function_list_) {
          if (language.compare(function_pointer->language_name_)) temporary_list.push_back(function_pointer);
        }
        function_list_ = temporary_list;

        RegisterFunctions(); 

      }
    }

    response->mutable_result()->set_boolean(true);

  }
  else {
    response->mutable_result()->set_boolean(false);
  }

  return return_value;

}

// Redundant UpdateGraphics removed, replaced by GraphicsHandler

void RJ2XCL_Engine::RemoveUserButton(const RJ2XCLBuffers::CallResponse &call, RJ2XCLBuffers::CallResponse &response) {
}

void RJ2XCL_Engine::ClearUserButtons() {
  ribbon_service_->ClearUserButtons();
}

HRESULT RJ2XCL_Engine::AddUserButtonInternal(const UserButton &button) {
  return ribbon_service_->AddUserButtonInternal(button);
}



int RJ2XCL_Engine::ExcelCallback(const RJ2XCLBuffers::CallResponse &call, RJ2XCLBuffers::CallResponse &response) {

  auto callback = call.function_call();
  int32_t command = 0;
  int32_t success = -1;

  if (callback.arguments_size() > 0) {
    auto arguments_array = callback.arguments(0).arr();

    int count = arguments_array.data().size();
    if (count > 0) {
      if (arguments_array.data(0).value_case() == RJ2XCLBuffers::Variable::ValueCase::kReal) command = (int32_t)arguments_array.data(0).real();
      else command = (int32_t)arguments_array.data(0).integer();
    }
    if (command) {
      ::rj2xcl::RaiiXlOper excel_result;
      std::vector<rj2xcl::RaiiXlOper> excel_arguments;
      std::vector<LPXLOPER12> excel_argument_pointers;

      if (count == 2 && arguments_array.data(1).value_case() == RJ2XCLBuffers::Variable::ValueCase::kArr) {
        auto argument_list = arguments_array.data(1).arr();
        int argument_list_count = argument_list.data_size();
        for (int i = 0; i < argument_list_count; i++) {
          rj2xcl::RaiiXlOper argument;
          Convert::VariableToXLOPER(argument.get(), argument_list.data(i));
          excel_arguments.push_back(std::move(argument));
          excel_argument_pointers.push_back(excel_arguments.back().get());
        }
      }
      else {
        for (int i = 1; i < count; i++) {
          rj2xcl::RaiiXlOper argument;
          Convert::VariableToXLOPER(argument.get(), arguments_array.data(i));
          excel_arguments.push_back(std::move(argument));
          excel_argument_pointers.push_back(excel_arguments.back().get());
        }
      }
      if (excel_arguments.size()) success = this->Excel()->Excel12v(command, &excel_result, (int32_t)excel_arguments.size(), excel_argument_pointers.data());
      else success = this->Excel()->Excel12(command, &excel_result, 0, 0);
      Convert::XLOPERToVariable(response.mutable_result(), &excel_result);
    }
  }

  return success;
}

/**
 * @brief Main initialization — called by xlAutoOpen when Excel loads the XLL.
 * 
 * Sequential flow (proven stable):
 * 1. Config + JobObject + language configuration
 * 2. Connect each engine sequentially (StartChildProcess + pipe retry)
 * 3. Send startup scripts (Initialize)
 * 4. Load user function files
 * 5. MapFunctions + RegisterFunctions (must happen during xlAutoOpen)
 */
void RJ2XCL_Engine::Init() {
  RJ2XCL_LOG_INFO("NEVEN: Engine::Init called");

  // Init objects (UI thread only — must happen before background work)
  Dispatcher()->RegisterHandler(std::make_unique<rj2xcl::GraphicsHandler>([this]() { return application_dispatch_; }));
  Dispatcher()->RegisterHandler(std::make_unique<rj2xcl::COMHandler>(object_map_));

  auto& config_service = rj2xcl::ConfigService::Instance();
  config_service.Initialize();

  // Register REPL language accessor for REPLBridge
  rj2xcl::RegisterREPLLanguageAccessor();

  auto config = config_service.GetConfig();
  auto home_directory = config_service.GetHomePath();
  auto dev_flags = config_service.GetDevFlags();

  auto language_config_result = config_service.ReadJsonFile(LANGUAGE_CONFIG_FILE_NAME);
  json11::Json language_config;
  if (language_config_result.is_success()) {
      language_config = language_config_result.value();
  }

  // Create JobObject for child process management
  if (config["NEVEN"]["useJobObject"].bool_value()) {
    job_handle_.reset(CreateJobObject(0, 0));
    JOBOBJECT_EXTENDED_LIMIT_INFORMATION jeli;

    memset(&jeli, 0, sizeof(jeli));
    jeli.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;

    if (job_handle_.is_valid()) {
      SetInformationJobObject(job_handle_.get(), JobObjectExtendedLimitInformation, &jeli, sizeof(jeli));
    }
  }

  auto& env = rj2xcl::EnvService::Instance();
  env.SetSystemMetadata(RJ2XCL_VERSION, __TIMESTAMP__);

  // Configure languages (non-blocking — just parses descriptors)
  auto& language_manager = rj2xcl::LanguageManager::Instance();
  language_manager.ConfigureLanguages(dev_flags, config, home_directory, language_config, callback_info_, object_map_);

  // ═══════════════════════════════════════════════════════════════════
  // Resolve functions directory (needed by background threads)
  // ═══════════════════════════════════════════════════════════════════
  std::string functions_directory = config["NEVEN"]["functionsDirectory"].string_value();
  if (functions_directory.length()) {
    functions_directory = env.ExpandEnvStrings(functions_directory);

    // Create the functions directory if it doesn't exist
    DWORD attrs = GetFileAttributesA(functions_directory.c_str());
    if (attrs == INVALID_FILE_ATTRIBUTES) {
      if (!CreateDirectoryA(functions_directory.c_str(), NULL)) {
        DWORD err = GetLastError();
        if (err == ERROR_PATH_NOT_FOUND) {
          std::string parent = functions_directory;
          std::vector<std::string> dirs_to_create;
          while (!parent.empty() && GetFileAttributesA(parent.c_str()) == INVALID_FILE_ATTRIBUTES) {
            dirs_to_create.push_back(parent);
            size_t pos = parent.find_last_of("\\/");
            if (pos == std::string::npos) break;
            parent = parent.substr(0, pos);
          }
          for (auto it = dirs_to_create.rbegin(); it != dirs_to_create.rend(); ++it) {
            CreateDirectoryA(it->c_str(), NULL);
          }
        }
      }
      RJ2XCL_LOG_INFO("Created functions directory: %s", functions_directory.c_str());

      // Copy example files if the directory was just created
      std::string examples_dir = home_directory + "examples\\";
      DWORD ex_attrs = GetFileAttributesA(examples_dir.c_str());
      if (ex_attrs != INVALID_FILE_ATTRIBUTES) {
        std::string src_r = examples_dir + "functions.r";
        std::string dst_r = functions_directory + "\\functions.r";
        CopyFileA(src_r.c_str(), dst_r.c_str(), TRUE);

        std::string src_jl = examples_dir + "functions.jl";
        std::string dst_jl = functions_directory + "\\functions.jl";
        CopyFileA(src_jl.c_str(), dst_jl.c_str(), TRUE);

        RJ2XCL_LOG_INFO("Copied example files to functions directory");
      }
    }

    // Re-enable file watch for hot-reload (AFTER zombie cleanup to avoid killing freshly launched processes)
    file_watch_service_->WatchDirectory(functions_directory, true);
  }

  // ═══════════════════════════════════════════════════════════════════
  // Kill orphaned child processes from previous sessions (zombie cleanup)
  // Uses taskkill via CreateProcess — non-blocking, no privilege issues.
  // MUST run BEFORE file_watch_service_->Start() and ConnectLanguages()
  // to avoid killing the processes we're about to launch.
  // ═══════════════════════════════════════════════════════════════════
  {
    const char* kill_cmds[] = {
      "taskkill /F /IM ControlR.exe /T",
      "taskkill /F /IM ControlJulia.exe /T",
      "taskkill /F /IM ControlPython.exe /T",
      nullptr
    };
    for (int i = 0; kill_cmds[i]; i++) {
      STARTUPINFOA si = {}; si.cb = sizeof(si); si.dwFlags = STARTF_USESHOWWINDOW; si.wShowWindow = SW_HIDE;
      PROCESS_INFORMATION pi = {};
      char cmd[256]; strncpy_s(cmd, kill_cmds[i], sizeof(cmd) - 1);
      if (CreateProcessA(NULL, cmd, NULL, NULL, FALSE, CREATE_NO_WINDOW, NULL, NULL, &si, &pi)) {
        WaitForSingleObject(pi.hProcess, 3000);
        CloseHandle(pi.hProcess); CloseHandle(pi.hThread);
      }
    }
    RJ2XCL_LOG_INFO("Zombie cleanup: killed orphaned ControlR/Julia/Python processes");
  }

  // Start file watcher AFTER zombie cleanup
  if (file_watch_service_) {
    file_watch_service_->Start();
  }

  // ═══════════════════════════════════════════════════════════════════
  // Connect engines and initialize (original stable flow via LanguageManager)
  // ═══════════════════════════════════════════════════════════════════
  language_manager.ConnectLanguages(job_handle_.get());
  language_manager.InitializeConnectedLanguages();

  // Load user function files for connected engines
  if (functions_directory.length()) {
    for (auto& svc : language_manager.GetServices()) {
      if (!svc->connected()) continue;

      WIN32_FIND_DATAA find_data;
      std::string search_pattern = functions_directory + "\\*.*";
      HANDLE hFind = FindFirstFileA(search_pattern.c_str(), &find_data);
      if (hFind != INVALID_HANDLE_VALUE) {
        do {
          if (find_data.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) continue;
          std::string file_path = functions_directory + "\\" + find_data.cFileName;
          if (svc->ValidFile(file_path)) {
            svc->ReadSourceFile(file_path);
          }
        } while (FindNextFileA(hFind, &find_data));
        FindClose(hFind);
      }
    }
  }

  // ═══════════════════════════════════════════════════════════════════
  // Map and register ALL functions during xlAutoOpen (the only safe context)
  // ═══════════════════════════════════════════════════════════════════
  MapFunctions();
  RegisterFunctions();

  // Console launch (non-blocking)
  bool start_console = false;
  std::string command_line_str = GetCommandLineA();
  if (command_line_str.find("/x:NEVEN") != std::string::npos || config["NEVEN"]["openConsole"].bool_value()) {
    start_console = true;
  }
  if (start_console || (dev_flags & 0x02)) {
    auto& wm = rj2xcl::WindowManager::Instance();
    wm.SetJobHandle(job_handle_.get());
    wm.ShowConsole();
  }

  // Initialize WebView2 viewer subsystem (async — does not block Excel)
  rj2xcl::ViewerManager::Instance().Initialize();

  // Initialize Pluto.jl manager (reads config, resolves Julia path)
  rj2xcl::PlutoManager::Instance().Initialize();

  // Health telemetry timer (every 5 minutes)
  SetTimer(NULL, 0, 300000, [](HWND, UINT, UINT_PTR timerId, DWORD) {
    rj2xcl::CrashHandler::WriteHealthSnapshot();
  });

  RJ2XCL_LOG_INFO("NEVEN: Init complete — all functions registered during xlAutoOpen");
}

void RJ2XCL_Engine::ScheduleDelayedUpdate() {
  // Historical note: Delayed re-registration was originally needed because
  // Julia's JIT compilation could delay function discovery. With the sysimage
  // approach (neven_julia.dll), Julia starts fast and functions are available
  // immediately. Python also completes startup synchronously (wait=true).
  //
  // The full UpdateFunctions() cycle (Unregister → MapFunctions → Register)
  // caused hangs when called from a Windows timer because xlGetName/xlfRegister
  // can fail outside of xlAutoOpen context, leading to all functions being
  // unregistered and not re-registered (error 2 = invalid xlfRegister).
  //
  // Solution: No delayed re-registration. All functions are registered during
  // xlAutoOpen which is the only safe context for xlfRegister.
  // If Julia files fail to load, the user can trigger =NEVEN.UpdateFunctions().

  // Only schedule periodic health telemetry (every 5 minutes)
  SetTimer(NULL, 0, 300000, [](HWND, UINT, UINT_PTR timerId, DWORD) {
    rj2xcl::CrashHandler::WriteHealthSnapshot();
  });
  
  RJ2XCL_LOG_INFO("Init complete — all functions registered during xlAutoOpen");
}

void RJ2XCL_Engine::RegisterLanguageCalls() {
  rj2xcl::LanguageManager::Instance().RegisterLanguageCalls();
}

void RJ2XCL_Engine::MapFunctions() {
  function_list_.clear();
  int index = 0;
  for (auto language_service : rj2xcl::LanguageManager::Instance().GetServices()) {
    FUNCTION_LIST functions = language_service->MapLanguageFunctions(index++, language_service);
    function_list_.insert(function_list_.end(), functions.begin(), functions.end());
  }
}

std::shared_ptr<LanguageService> RJ2XCL_Engine::GetLanguageService(uint32_t key) {
  return rj2xcl::LanguageManager::Instance().GetLanguageService(key);
}

/** IMPLEMENTATION: Resolved S4-H2 */
void RJ2XCL_Engine::ExecUserButton(uint32_t id, const std::string &language) {
  
  std::shared_ptr<LanguageService> service = rj2xcl::LanguageManager::Instance().GetLanguageService(language);
  if (service) {
    RJ2XCLBuffers::CallResponse call, response;
    call.set_wait(true);
    call.set_user_command(id);
    service->Call(response, call);
  }

}

void RJ2XCL_Engine::CallLanguage(uint32_t language_key, RJ2XCLBuffers::CallResponse &response, RJ2XCLBuffers::CallResponse &call) {
  rj2xcl::LanguageManager::Instance().CallLanguage(language_key, response, call);
}

void RJ2XCL_Engine::Close() {

  // Shutdown Pluto server first (if running)
  rj2xcl::PlutoManager::Instance().Shutdown();

  // Shutdown WebView2 viewer subsystem
  rj2xcl::ViewerManager::Instance().Shutdown();

  file_watch_service_->Stop();
  ShutdownConsole();
  rj2xcl::LanguageManager::Instance().Shutdown();

  LPDISPATCH dispatch_pointer = application_dispatch_;
  if (dispatch_pointer) dispatch_pointer->Release();

  // UniqueHandle automagically closes job_handle_ and others

}

extern "C" {

  // Global initialization flag (reset in xlAutoClose)
  bool g_neven_initialized = false;

  __declspec(dllexport) int __stdcall xlAutoOpen(void) {
    // Guard against double initialization (Excel may call xlAutoOpen twice)
    if (g_neven_initialized) {
        RJ2XCL_LOG_WARN("xlAutoOpen called again — skipping duplicate initialization");
        return 1;
    }
    g_neven_initialized = true;

    // Initialize logging — use module directory
    std::string logPath = ModuleFunctions::ModulePath() + "neven.log";
    rj2xcl::LogService::Instance().Initialize(logPath);
    RJ2XCL_LOG_INFO("xlAutoOpen called");

    // Install crash telemetry — captures unhandled exceptions
    rj2xcl::CrashHandler::Install();

    // Attempt to hook Excel Entry Point
    HMODULE hExcel = GetModuleHandle(NULL); // Excel.exe
    MDCALLBACK12PROC pEntry = (MDCALLBACK12PROC)GetProcAddress(hExcel, "MdCallBack12");

    if (pEntry) {
        SetExcel12EntryPt(pEntry);
        RJ2XCL_Engine::Instance()->Init();
    } else {
        MessageBoxA(NULL, "CRITICAL: MdCallBack12 not found!", "NEVEN", MB_ICONERROR);
    }

    return 1;
  }



  /** standard excel export */
  __declspec(dllexport) int __stdcall xlAutoClose(void) {
    rj2xcl::CrashHandler::WriteHealthSnapshot();  // Final health snapshot
    rj2xcl::CrashHandler::Uninstall();

    // Cancel any in-progress background initialization (max 5s wait)
    neven::InitOrchestrator::Instance().CancelAndWait(5000);

    RJ2XCL_Engine::Instance()->Close();

    // Reset initialization guard so xlAutoOpen works if Excel reloads the XLL
    // without fully unloading the DLL (e.g., COM Add-in keeps reference)
    g_neven_initialized = false;

    return 1;
  }

  /** standard excel export */
  __declspec(dllexport) void __stdcall xlAutoFree12(LPXLOPER12 px) {
    if (px->xltype & xlbitDLLFree) {
      // iterate over arrays if necessary
      if (px->xltype & xltypeMulti) {
        px->xltype = xltypeRef | xlbitDLLFree;
        int count = px->val.array.rows * px->val.array.columns;
        for (int i = 0; i < count; i++) {
          if (px->val.array.lparray[i].xltype & xltypeStr) {
            delete[] px->val.array.lparray[i].val.str;
          }
        }
        delete[] px->val.array.lparray;
      }
      else if (px->xltype & xltypeStr) {
        delete[] px->val.str;
      }
    }
  }

  /** standard excel export */
  __declspec(dllexport) LPXLOPER12 __stdcall xlAddInManagerInfo12(LPXLOPER12 pxAction) {
    static XLOPER12 xInfo, xIntAction;
    LPXLOPER12 pxRet = 0;
    
    RJ2XCL_Engine::Instance()->Excel()->Excel12(xlCoerce, &xIntAction, 2, pxAction, TempInt12(xltypeInt));
    if (xIntAction.val.w == 1) {
      xInfo.xltype = xltypeStr;
      xInfo.val.str = L"\005NEVEN"; // Pascal-style string: length + data
      pxRet = &xInfo;
    }
    else {
      xInfo.xltype = xltypeErr;
      xInfo.val.err = xlerrValue;
      pxRet = &xInfo;
    }
    return pxRet;
  }

}
