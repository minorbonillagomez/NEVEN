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
#include <string>
#include <vector>
#include <sstream>

#include "XLCALL.h"
#include "excel_api_functions.h"
#include "basic_functions.h"
#include "type_conversions.h"
#include "rj2xcl.h"
#include "rj2xcl_graphics.h"
#include "LanguageManager.h"
#include "RaiiXlOper.h"

#include "excel_com_type_libraries.h"

#include "..\resource.h"

void UnregisterFunctions() {

  auto engine = RJ2XCL_Engine::Instance();
  rj2xcl::RaiiXlOper xlParm;

  for (auto entry : engine->function_list_) {
    if (entry->register_id_) {
      xlParm->xltype = xltypeNum;
      xlParm->val.num = entry->register_id_;
      engine->Excel()->Excel12(xlfUnregister, 0, 1, &xlParm);
      entry->register_id_ = 0;
    }
  }
}

/**
 * @brief Registers core NEVEN worksheet functions and language-specific Exec/Call shortcuts with Excel.
 *
 * Phase 1 registers built-in functions (Console, Version, View, etc.) from funcTemplates.
 * Phase 2 registers per-language NEVEN.<prefix> and NEVEN.<prefix>.Call functions.
 */
void RegisterBasicFunctions() {
  auto engine = RJ2XCL_Engine::Instance();
  RJ2XCL_LOG_INFO("RJ2XCL: RegisterBasicFunctions started");

  // Get the DLL name for registration (required as first param of xlfRegister)
  // Method 1: Ask Excel via xlGetName
  XLOPER12 xlDllName;
  memset(&xlDllName, 0, sizeof(xlDllName));
  xlDllName.xltype = xltypeNil;
  int nameErr = engine->Excel()->Excel12(xlGetName, &xlDllName, 0);

  // If xlGetName fails, try xltypeMissing which tells Excel to use current XLL
  XLOPER12 xlMissing;
  xlMissing.xltype = xltypeMissing;

  LPXLOPER12 pDllName = &xlDllName;
  if (nameErr || xlDllName.xltype != xltypeStr) {
    // xlGetName failed — this happens when loaded via COM add-in
    // Use the module path directly
    extern HMODULE global_module_handle;
    wchar_t modulePath[MAX_PATH];
    if (GetModuleFileNameW(global_module_handle, modulePath, MAX_PATH)) {
      // Fix extension: compiled as .dll but loaded as .xll
      wchar_t *ext = wcsrchr(modulePath, L'.');
      if (ext && (_wcsicmp(ext, L".dll") == 0)) {
        wcscpy_s(ext, 5, L".xll");
      }
      int len = (int)wcslen(modulePath);
      // Excel expects Pascal-style wide string (length prefix)
      static wchar_t pascalStr[MAX_PATH + 2];
      pascalStr[0] = (wchar_t)len;
      memcpy(pascalStr + 1, modulePath, len * sizeof(wchar_t));
      pascalStr[len + 1] = 0;
      xlDllName.xltype = xltypeStr;
      xlDllName.val.str = pascalStr;
      pDllName = &xlDllName;
    }
  }

  // Phase 1: Core basic functions (Console, Version, etc.)
  for (int i = 0; funcTemplates[i][0]; i++) {
    rj2xcl::RaiiXlOper xlRegisterID;
    rj2xcl::RaiiXlOper xlParms[10];
    LPXLOPER12 xlParmPtrs[10];

    // First param must be the DLL path
    xlParmPtrs[0] = pDllName;

    for (int j = 0; j < 9; j++) {
      if (funcTemplates[i][j] && funcTemplates[i][j][0]) {
        Convert::StringToXLOPER(&xlParms[j + 1], funcTemplates[i][j], true);
      } else {
        xlParms[j + 1]->xltype = xltypeNil;
      }
      xlParmPtrs[j + 1] = &xlParms[j + 1];
    }

    int err = engine->Excel()->Excel12v(xlfRegister, &xlRegisterID, 10, xlParmPtrs);
    if (err) {
      RJ2XCL_LOG_ERR("ERR register basic function %d: %d (export: %ls, type: %ls)", 
          i, err, funcTemplates[i][0], funcTemplates[i][1]);
    }
  }

  // Phase 1b: RJ2XCL.QUARTO — registered as worksheet function (type 1).
  // Renders .qmd files via CreateProcess("quarto render") and opens in WebView2.

  // Phase 2: Language specific Exec/Call shortcuts (NEVEN.r, NEVEN.j, etc.)
  auto& lm = rj2xcl::LanguageManager::Instance();
  int lang_index = 0;
  for (auto service : lm.GetServices()) {
      if (lang_index >= 16) break; // Limit to placeholders available

      std::string prefix = service->prefix();
      if (prefix.empty()) {
          lang_index++;
          continue;
      }

      rj2xcl::RaiiXlOper xlRegisterID;
      rj2xcl::RaiiXlOper xlParms[12];
      LPXLOPER12 xlParmPtrs[12];
      xlParmPtrs[0] = pDllName; // Use DLL name
      for (int k = 0; k < 12; k++) {
          xlParms[k]->xltype = xltypeNil;
          if (k > 0) xlParmPtrs[k] = &xlParms[k];
      }

      // Register Exec: NEVEN.<prefix>
      std::string exec_func_name = "NEVEN." + prefix;
      std::stringstream ss_export;
      ss_export << "RJ_ExecLanguage_" << (1000 + lang_index);

      Convert::StringToXLOPER(&xlParms[1], ss_export.str().c_str(), true);
      Convert::StringToXLOPER(&xlParms[2], L"UQ", true);
      Convert::StringToXLOPER(&xlParms[3], exec_func_name.c_str(), true);
      Convert::StringToXLOPER(&xlParms[4], L"Code", true);
      Convert::StringToXLOPER(&xlParms[5], L"1", true);
      Convert::StringToXLOPER(&xlParms[6], L"NEVEN", true);
      Convert::StringToXLOPER(&xlParms[10], L"Code to execute", true);

      engine->Excel()->Excel12v(xlfRegister, &xlRegisterID, 11, xlParmPtrs);

      // Register Call: NEVEN.<prefix>.Call
      std::string call_func_name = "NEVEN." + prefix + ".Call";
      ss_export.str("");
      ss_export.clear();
      ss_export << "RJ_CallLanguage_" << (1000 + lang_index);

      // Re-init for second registration
      for (int k = 0; k < 12; k++) xlParms[k].Free();

      Convert::StringToXLOPER(&xlParms[1], ss_export.str().c_str(), true);
      Convert::StringToXLOPER(&xlParms[2], L"UQQQQQQQQQQQQQQQQQ", true);
      Convert::StringToXLOPER(&xlParms[3], call_func_name.c_str(), true);
      Convert::StringToXLOPER(&xlParms[4], L"Function, Args...", true);
      Convert::StringToXLOPER(&xlParms[5], L"1", true);
      Convert::StringToXLOPER(&xlParms[6], L"NEVEN", true);

      engine->Excel()->Excel12v(xlfRegister, &xlRegisterID, 11, xlParmPtrs);

      lang_index++;
  }
}

/**
 * @brief Registers all worksheet functions with Excel (basic + dynamically exported R/Julia functions).
 *
 * Calls RegisterBasicFunctions() first, then iterates the engine's function_list_
 * to register each exported language function via xlfRegister.
 */
void RegisterFunctions() {

  RegisterBasicFunctions();

  rj2xcl::RaiiXlOper xlParms[32];
  LPXLOPER12 xlParmPtrs[32];
  rj2xcl::RaiiXlOper xlRegisterID;
  int err;

  auto engine = RJ2XCL_Engine::Instance();
  for (int i = 0; i < 32; i++) {
    xlParms[i]->xltype = xltypeMissing;
    xlParmPtrs[i] = xlParms[i].get();
  }

  // Get DLL name — use same fallback as RegisterBasicFunctions
  XLOPER12 xlDllNameForReg;
  memset(&xlDllNameForReg, 0, sizeof(xlDllNameForReg));
  xlDllNameForReg.xltype = xltypeNil;
  err = engine->Excel()->Excel12(xlGetName, &xlDllNameForReg, 0);
  if (err || xlDllNameForReg.xltype != xltypeStr) {
    RJ2XCL_LOG_WARN("xlGetName failed in RegisterFunctions, using fallback");
    extern HMODULE global_module_handle;
    wchar_t modulePath[MAX_PATH];
    if (GetModuleFileNameW(global_module_handle, modulePath, MAX_PATH)) {
      wchar_t *ext = wcsrchr(modulePath, L'.');
      if (ext && (_wcsicmp(ext, L".dll") == 0)) wcscpy_s(ext, 5, L".xll");
      int len = (int)wcslen(modulePath);
      static wchar_t pascalStr2[MAX_PATH + 2];
      pascalStr2[0] = (wchar_t)len;
      memcpy(pascalStr2 + 1, modulePath, len * sizeof(wchar_t));
      pascalStr2[len + 1] = 0;
      xlDllNameForReg.xltype = xltypeStr;
      xlDllNameForReg.val.str = pascalStr2;
    }
  }
  xlParmPtrs[0] = &xlDllNameForReg;
  int index = 1000;

  for (auto entry : engine->function_list_) {

    auto language_service = rj2xcl::LanguageManager::Instance().GetLanguageService(entry->language_key_);

    std::stringstream ss;

    ss.clear();
    ss.str("");
    ss << "RJ_FunctionCall" << index;
    Convert::StringToXLOPER(xlParmPtrs[1], ss.str(), false);
    Convert::StringToXLOPER(xlParmPtrs[2], "UQQQQQQQQQQQQQQQQ", false);

    ss.clear();
    ss.str("");

    // using alias here instead of name; call will still use name.

    ss << language_service->prefix();
    ss << ".";
    if (entry->alias_.length()) ss << entry->alias_;
    else ss << entry->name_;
    Convert::StringToXLOPER(xlParmPtrs[3], ss.str(), false);

    ss.clear();
    ss.str("");
    for (auto arg : entry->arguments_) ss << ", " << arg->name_;
    Convert::StringToXLOPER(xlParmPtrs[4], ss.str().c_str() + 2, false);

    Convert::StringToXLOPER(xlParmPtrs[5], "1", false);

    ss.clear();
    ss.str("");
    if (entry->category_.length()) ss << entry->category_;
    else ss << "Exported " << language_service->name() << " Functions";
    Convert::StringToXLOPER(xlParmPtrs[6], ss.str().c_str(), false);

    ss.clear();
    ss.str("");
    ss << index;
    Convert::StringToXLOPER(xlParmPtrs[8], ss.str(), false);

    if(entry->description_.length()) {
      // Excel xlfRegister limits description to 255 chars
      std::string desc = entry->description_;
      if (desc.length() > 253) desc = desc.substr(0, 250) + "...";
      // Remove newlines (Excel doesn't support them in function descriptions)
      for (auto& c : desc) { if (c == '\n' || c == '\r') c = ' '; }
      Convert::StringToXLOPER(xlParmPtrs[9], desc, false);
    }
    else Convert::StringToXLOPER(xlParmPtrs[9], "Exported Function", false);

    for (uint32_t i = 0; i < entry->arguments_.size(); i++) {
      if (entry->arguments_[i]->description_.length()) Convert::StringToXLOPER(xlParmPtrs[10 + i], entry->arguments_[i]->description_, false);
      else Convert::StringToXLOPER(xlParmPtrs[10 + i], "Argument", false);
    }

    err = engine->Excel()->Excel12v(xlfRegister, &xlRegisterID, 10 + (int32_t)entry->arguments_.size(), xlParmPtrs);
    if (!err && xlRegisterID->xltype == xltypeNum) {
      entry->register_id_ = xlRegisterID->val.num;
      RJ2XCL_LOG_DEBUG("Registered function %d: %s.%s (%d args)", index,
          language_service->prefix().c_str(), entry->name_.c_str(), (int)entry->arguments_.size());
    }
    else {
      RJ2XCL_LOG_ERR("ERR register function %d: %d (name: %s.%s, args: %d)", index, err,
          language_service->prefix().c_str(), entry->name_.c_str(), (int)entry->arguments_.size());
    }
    index++;
  }

}

LPXLOPER12 RJ2XCLFunctionCall(uint32_t index, LPXLOPER12 *args, int32_t count) {

  static XLOPER12 xlResult;
  xlResult.xltype = xltypeNil;

  auto engine = RJ2XCL_Engine::Instance();

  if (index < 1000 || (index - 1000) >= engine->function_list_.size()) return &xlResult;

  auto entry = engine->function_list_[index - 1000];
  auto language_service = rj2xcl::LanguageManager::Instance().GetLanguageService(entry->language_key_);

  if (language_service) {

    RJ2XCLBuffers::CallResponse call, response;
    call.set_wait(true);
    call.set_id(0);

    auto function_call = call.mutable_function_call();
    function_call->set_target(RJ2XCLBuffers::CallTarget::language);
    function_call->set_function(entry->name_);
    function_call->set_index(entry->language_key_);

    for (int i = 0; i < count; i++) {
        Convert::XLOPERToVariable(function_call->add_arguments(), args[i]);
    }

    language_service->Call(response, call);
    Convert::VariableToXLOPER(&xlResult, response.result());
    xlResult.xltype |= xlbitDLLFree;

  }

  return &xlResult;

}

void ClearUserButtons(LPDISPATCH ribbon_dispatch) {
  auto engine = RJ2XCL_Engine::Instance();
  engine->ClearUserButtons();
}

void RJ2XCLUserButton(uint32_t id, const char *language) {
  auto engine = RJ2XCL_Engine::Instance();
  engine->ExecUserButton(id, language);
}

void RJ2XCLContextSwitch(const char *language) {
  // auto engine = RJ2XCL_Engine::Instance();
}

void RJ2XCLUpdateFunctions() {
  auto engine = RJ2XCL_Engine::Instance();
  engine->UpdateFunctions();
}

