/**
 * Copyright (c) 2026 RJ2XCL Project
 * 
 * This file is part of RJ2XCL.
 */

#include "stdafx.h"
#include "RibbonService.h"
#include "rj2xcl.h"
#include <sstream>

namespace rj2xcl {

  // Helper to convert UTF-8 string to wstring
  std::wstring Utf8ToWide(const std::string& str) {
    if (str.empty()) return L"";
    int size_needed = MultiByteToWideChar(CP_UTF8, 0, &str[0], (int)str.size(), NULL, 0);
    std::wstring wstrTo(size_needed, 0);
    MultiByteToWideChar(CP_UTF8, 0, &str[0], (int)str.size(), &wstrTo[0], size_needed);
    return wstrTo;
  }

  RibbonService::RibbonService() 
    : next_user_button_id_(1000) {
  }

  void RibbonService::SetRibbonPointer(LPDISPATCH ribbon_pointer) {
    ribbon_menu_dispatch_ = ribbon_pointer;
    
    if (pending_user_buttons_.size() > 0) {
      for (const auto &button : pending_user_buttons_) {
        AddUserButtonInternal(button);
      }
      pending_user_buttons_.clear();
    }
  }

  int RibbonService::AddUserButton(const RJ2XCLBuffers::CallResponse &call, 
                                 RJ2XCLBuffers::CallResponse &response, 
                                 const std::string &language) {
    
    if (!call.has_function_call()) return -1;
    const auto &callback = call.function_call();

    UserButton button;
    button.id_ = next_user_button_id_++;
    button.language_tag_ = Utf8ToWide(language);

    for (int i = 0; i < callback.arguments_size(); i++) {
      const auto &arg = callback.arguments(i);
      if (i == 0) button.label_ = Utf8ToWide(arg.str());
      else if (i == 1) button.image_mso_ = Utf8ToWide(arg.str());
      else if (i == 2) button.tip_ = Utf8ToWide(arg.str());
    }

    if (ribbon_menu_dispatch_) {
      AddUserButtonInternal(button);
    } else {
      pending_user_buttons_.push_back(button);
    }

    response.mutable_result()->set_integer(button.id_);
    return 0;
  }

  void RibbonService::ExecUserButton(uint32_t id, const std::string &language) {
    // This usually triggers an Excel function call back into the XLL
    // but the implementation logic resides in the Ribbon side (VBA/COM).
    // The engine just provides the gateway.
  }

  void RibbonService::ClearUserButtons() {
    if (!ribbon_menu_dispatch_) {
      pending_user_buttons_.clear();
      return;
    }

    DISPID dispid;
    CComBSTR function = L"ClearUserButtons";
    HRESULT hresult = ribbon_menu_dispatch_->GetIDsOfNames(IID_NULL, &function.m_str, 1, 1033, &dispid);

    if (SUCCEEDED(hresult)) {
      DISPPARAMS dispparams = {0};
      CComVariant cvResult;
      ribbon_menu_dispatch_->Invoke(dispid, IID_NULL, 1033, DISPATCH_METHOD, &dispparams, &cvResult, NULL, NULL);
    }
  }

  HRESULT RibbonService::AddUserButtonInternal(const UserButton &button) {
    if (!ribbon_menu_dispatch_) return E_FAIL;

    DISPID dispid;
    CComBSTR function = L"AddUserButton";
    HRESULT hresult = ribbon_menu_dispatch_->GetIDsOfNames(IID_NULL, &function.m_str, 1, 1033, &dispid);

    if (FAILED(hresult)) return hresult;

    std::vector<CComVariant> com_arguments;
    // Arguments are passed in reverse order for Invoke
    com_arguments.push_back(CComVariant(button.id_));
    com_arguments.push_back(CComVariant(button.language_tag_.c_str()));
    com_arguments.push_back(CComVariant(button.image_mso_.c_str()));
    com_arguments.push_back(CComVariant(button.label_.c_str()));
    com_arguments.push_back(CComVariant(button.tip_.c_str()));

    DISPPARAMS dispparams;
    dispparams.cArgs = (UINT)com_arguments.size();
    dispparams.cNamedArgs = 0;
    dispparams.rgvarg = com_arguments.data();

    return ribbon_menu_dispatch_->Invoke(dispid, IID_NULL, 1033, DISPATCH_METHOD, &dispparams, NULL, NULL, NULL);
  }

} // namespace rj2xcl
