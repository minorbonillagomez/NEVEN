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

#define _ATL_NO_DEBUG_CRT

#include <cstdint>
#include <atlbase.h>
#include <atlcom.h>
#include <atlsafe.h>
#include <vector>
#include <string>
#include "variable.pb.h"

#include <unordered_map>

#include "json11.hpp"

#include "function_descriptor.h"
#include "rj2xcl_graphics.h"
#include "com_object_map.h"
#include "language_service.h"
#include "callback_info.h"
#include "file_change_watcher.h"
#include "user_button.h"
#include "ConfigService.h"
#include "LanguageManager.h"
#include "WindowManager.h"
#include "IExcelBridge.h"
#include "CallbackDispatcher.h"
#include "RibbonService.h"
#include "FileWatchService.h"
#include "UniqueHandle.h"
#include <memory>

#define CONFIG_FILE_NAME "neven-config.json"
#define LANGUAGE_CONFIG_FILE_NAME "neven-languages.json"

class RJ2XCL_Engine {

private:
  /** the single instance */
  static RJ2XCL_Engine *instance_;

private:

  /** ribbon management service */
  std::unique_ptr<rj2xcl::RibbonService> ribbon_service_;

  /** generated object map */
  COMObjectMap object_map_;

  /** marshalled excel pointer for calls from separate threads */
  IStream *stream_pointer_;

  /** excel COM pointer */
  LPDISPATCH application_dispatch_;

  CallbackInfo callback_info_;

  /**
   * handle to the job object we use to manage child-processes (it
   * will kill all children when the parent process exits for any
   * reason -- reducing zombies)
   */
  rj2xcl::UniqueHandle job_handle_;


  /** watch file changes */
  std::unique_ptr<rj2xcl::FileWatchService> file_watch_service_;

  /** excel sdk bridge */
  std::unique_ptr<rj2xcl::IExcelBridge> excel_bridge_;

  /** callback dispatcher */
  std::unique_ptr<rj2xcl::CallbackDispatcher> callback_dispatcher_;


public:

  /** excel sdk bridge accessor */
  rj2xcl::IExcelBridge* Excel() { return excel_bridge_.get(); }

  /** job handle accessor (for on-demand language connection) */
  HANDLE GetJobHandle() { return job_handle_.get(); }

  /** callback dispatcher accessor */
  rj2xcl::CallbackDispatcher* Dispatcher() { return callback_dispatcher_.get(); }

  /** ribbon service accessor */
  rj2xcl::RibbonService* Ribbon() { return ribbon_service_.get(); }

  /** file watch service accessor */
  rj2xcl::FileWatchService* FileWatch() { return file_watch_service_.get(); }

  /** application dispatch pointer accessor (for deferred SetApplicationPointer calls) */
  LPDISPATCH GetApplicationDispatch() const { return application_dispatch_; }

  /** set bridge (for testing) */
  void SetBridge(std::unique_ptr<rj2xcl::IExcelBridge> bridge) { excel_bridge_ = std::move(bridge); }

  /** mapped functions */
  FUNCTION_LIST function_list_;

private:
  /** constructors are private (singleton) */
  RJ2XCL_Engine();

  /** constructors are private (singleton) */
  RJ2XCL_Engine(RJ2XCL_Engine const&) {};

  /** constructors are private (singleton) */
  RJ2XCL_Engine& operator = (RJ2XCL_Engine const&) {};

private:
  // File watch logic moved to FileWatchService

protected:

  void ShutdownConsole();


public:

  void RegisterLanguageCalls();
  std::shared_ptr<LanguageService> GetLanguageService(uint32_t key);
  void CallLanguage(uint32_t language_key, RJ2XCLBuffers::CallResponse &response, RJ2XCLBuffers::CallResponse &call);

public:

  /** handles callback functions from R */
  void HandleCallback(const std::string &language);

public:

  /** single static instance of this class */
  static RJ2XCL_Engine* Instance();

  /**
   * @brief Resets the engine singleton instance for unit testing isolation.
   * @note Only intended to be called from the test suite.
   */
  void ResetForTesting();

public:

  /** sets COM pointers */
  void SetPointers(ULONG_PTR excel_pointer, ULONG_PTR ribbon_pointer);

  /* window management moved to WindowManager */


  /** 
   * opens the console, creating the process if necessary 
   */
  void ShowConsole();

  /**
   * hides the console, without actually closing the process
   */
  void HideConsole();

  /** initializes; starts R, threads, pipes */
  void Init();

  /** shuts down pipes and processes */
  void Close();

  /** mapped functions */
  void MapFunctions();

  /** registration. maps and registers functions. */
  int UpdateFunctions();

  /** Schedule a delayed re-registration via xlcOnTime timer. */
  void ScheduleDelayedUpdate();

  /** Excel API function callback */
  int ExcelCallback(const RJ2XCLBuffers::CallResponse &call, RJ2XCLBuffers::CallResponse &response);

  HRESULT AddUserButtonInternal(const UserButton &button);

  /** */
  int AddUserButton(const RJ2XCLBuffers::CallResponse &call, RJ2XCLBuffers::CallResponse &response, const std::string &language);

  /** */
  void RemoveUserButton(const RJ2XCLBuffers::CallResponse &call, RJ2XCLBuffers::CallResponse &response);

  /** */
  void ExecUserButton(uint32_t id, const std::string &language);

  /** handles callback functions from R/Julia on a separate thread */
  int HandleCallbackOnThread(const std::string &language, const RJ2XCLBuffers::CallResponse *call = 0, RJ2XCLBuffers::CallResponse *response = 0);

  /** DELEGATED: removes all user buttons */
  void ClearUserButtons();

};
