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

#pragma once

#include "resource.h"       // main symbols

#include <atlsafe.h>
#include <Gdiplus.h>

#include "../Common/user_button.h"
#include <vector>

typedef IDispatchImpl<IRibbonExtensibility, &__uuidof(IRibbonExtensibility), &LIBID_Office, /* wMajor = */ 2, /* wMinor = */ 4> RIBBON_INTERFACE;
typedef int(*SetPointersProcedure)(ULONG_PTR, ULONG_PTR);

typedef enum {

  ShowConsole = 1001,
  ShowRTerminal,
  ShowJuliaTerminal,
  GetImage,
  GetLabel,

  UpdateRibbon,
  AddUserButton,
  ClearUserButtons,

  GetUserButtonImage,
  GetUserButtonVisible,
  GetUserButtonsVisible,
  GetUserButtonLabel,
  GetUserButtonTip,
  UserButtonAction,

  RibbonLoaded,

  // New NEVEN v2.0 commands
  OnPlutoStart,
  OnPlutoStop,
  OnViewDialog,
  OnEditor,
  OnCloseViewers,
  OnNotebookDialog,
  OnQuartoDialog,
  OnRefreshFunctions,
  OnOpenScriptsDir,
  OnOpenConfig,
  OnAbout,
  OnViewerList,
  OnInstallPkgR,
  OnInstallPkgJulia,
  OnListPkgR,
  OnListPkgJulia,
  OnOpenDocs,

} DispIds;

// CConnect
class ATL_NO_VTABLE CConnect :
  public CComObjectRootEx<CComSingleThreadModel>,
  public CComCoClass<CConnect, &CLSID_Connect>,
  public IDispatchImpl<AddInDesignerObjects::_IDTExtensibility2, &AddInDesignerObjects::IID__IDTExtensibility2, &AddInDesignerObjects::LIBID_AddInDesignerObjects, 1, 0>,
  public RIBBON_INTERFACE
{
public:
  CConnect() : m_pApplication(0)
  {
  }

  DECLARE_REGISTRY_RESOURCEID(IDR_NEVENRIBBON)
  DECLARE_NOT_AGGREGATABLE(CConnect)

  BEGIN_COM_MAP(CConnect)
    COM_INTERFACE_ENTRY2(IDispatch, IRibbonExtensibility)
    COM_INTERFACE_ENTRY(AddInDesignerObjects::_IDTExtensibility2)
    COM_INTERFACE_ENTRY(IRibbonExtensibility)
  END_COM_MAP()

  DECLARE_PROTECT_FINAL_CONSTRUCT()

  HRESULT FinalConstruct()
  {
    return S_OK;
  }

  void FinalRelease()
  {
  }

public:

public:
  //IDTExtensibility2 implementation:
  STDMETHOD(OnConnection)(IDispatch * Application, AddInDesignerObjects::ext_ConnectMode ConnectMode, IDispatch *AddInInst, SAFEARRAY **custom);
  STDMETHOD(OnDisconnection)(AddInDesignerObjects::ext_DisconnectMode RemoveMode, SAFEARRAY **custom);
  STDMETHOD(OnAddInsUpdate)(SAFEARRAY **custom);
  STDMETHOD(OnStartupComplete)(SAFEARRAY **custom);
  STDMETHOD(OnBeginShutdown)(SAFEARRAY **custom);

  STDMETHOD(GetImage)(int32_t image_id, VARIANT *result);

  CComPtr<IDispatch>      m_pApplication;
  CComPtr<IDispatch>      m_pAddInInstance;
  CComQIPtr<IRibbonUI>    m_pRibbonUI;

  std::vector<UserButton> user_buttons_;

  // IRibbonExtensibility methods
  STDMETHOD(GetCustomUI)(BSTR RibbonID, BSTR *pbstrRibbonXML);

  // IDispatch methods
  STDMETHOD(GetIDsOfNames)(REFIID riid, LPOLESTR* rgszNames, UINT cNames, LCID lcid, DISPID* rgdispid) {

    int disp_id = 0;

    if (cNames > 0) {
      if (!wcscmp(rgszNames[0], L"ShowConsole")) disp_id = DispIds::ShowConsole;
      else if (!wcscmp(rgszNames[0], L"ShowRTerminal")) disp_id = DispIds::ShowRTerminal;
      else if (!wcscmp(rgszNames[0], L"ShowJuliaTerminal")) disp_id = DispIds::ShowJuliaTerminal;
      else if (!wcscmp(rgszNames[0], L"GetImage")) disp_id = DispIds::GetImage;
      else if (!wcscmp(rgszNames[0], L"GetLabel")) disp_id = DispIds::GetLabel;
      else if (!wcscmp(rgszNames[0], L"GetUserButtonImage")) disp_id = DispIds::GetUserButtonImage;
      else if (!wcscmp(rgszNames[0], L"GetUserButtonVisible")) disp_id = DispIds::GetUserButtonVisible;
      else if (!wcscmp(rgszNames[0], L"GetUserButtonsVisible")) disp_id = DispIds::GetUserButtonsVisible;
      else if (!wcscmp(rgszNames[0], L"GetUserButtonLabel")) disp_id = DispIds::GetUserButtonLabel;
      else if (!wcscmp(rgszNames[0], L"GetUserButtonTip")) disp_id = DispIds::GetUserButtonTip;
      else if (!wcscmp(rgszNames[0], L"UserButtonAction")) disp_id = DispIds::UserButtonAction;
      else if (!wcscmp(rgszNames[0], L"UpdateRibbon")) disp_id = DispIds::UpdateRibbon;
      else if (!wcscmp(rgszNames[0], L"AddUserButton")) disp_id = DispIds::AddUserButton;
      else if (!wcscmp(rgszNames[0], L"ClearUserButtons")) disp_id = DispIds::ClearUserButtons;
      else if (!wcscmp(rgszNames[0], L"RibbonLoaded")) disp_id = DispIds::RibbonLoaded;
      else if (!wcscmp(rgszNames[0], L"OnPlutoStart")) disp_id = DispIds::OnPlutoStart;
      else if (!wcscmp(rgszNames[0], L"OnPlutoStop")) disp_id = DispIds::OnPlutoStop;
      else if (!wcscmp(rgszNames[0], L"OnViewDialog")) disp_id = DispIds::OnViewDialog;
      else if (!wcscmp(rgszNames[0], L"OnEditor")) disp_id = DispIds::OnEditor;
      else if (!wcscmp(rgszNames[0], L"OnCloseViewers")) disp_id = DispIds::OnCloseViewers;
      else if (!wcscmp(rgszNames[0], L"OnNotebookDialog")) disp_id = DispIds::OnNotebookDialog;
      else if (!wcscmp(rgszNames[0], L"OnQuartoDialog")) disp_id = DispIds::OnQuartoDialog;
      else if (!wcscmp(rgszNames[0], L"OnRefreshFunctions")) disp_id = DispIds::OnRefreshFunctions;
      else if (!wcscmp(rgszNames[0], L"OnOpenScriptsDir")) disp_id = DispIds::OnOpenScriptsDir;
      else if (!wcscmp(rgszNames[0], L"OnOpenConfig")) disp_id = DispIds::OnOpenConfig;
      else if (!wcscmp(rgszNames[0], L"OnAbout")) disp_id = DispIds::OnAbout;
      else if (!wcscmp(rgszNames[0], L"OnViewerList")) disp_id = DispIds::OnViewerList;
      else if (!wcscmp(rgszNames[0], L"OnInstallPkgR")) disp_id = DispIds::OnInstallPkgR;
      else if (!wcscmp(rgszNames[0], L"OnInstallPkgJulia")) disp_id = DispIds::OnInstallPkgJulia;
      else if (!wcscmp(rgszNames[0], L"OnListPkgR")) disp_id = DispIds::OnListPkgR;
      else if (!wcscmp(rgszNames[0], L"OnListPkgJulia")) disp_id = DispIds::OnListPkgJulia;
      else if (!wcscmp(rgszNames[0], L"OnOpenDocs")) disp_id = DispIds::OnOpenDocs;
    }

    if (disp_id > 0)
    {
      rgdispid[0] = disp_id;
      return S_OK;
    }

    return RIBBON_INTERFACE::GetIDsOfNames(riid, rgszNames, cNames, lcid, rgdispid);
  }

  int ButtonTag(DISPPARAMS* pdispparams) {

    int tag = -1; // invalid
    if (pdispparams->cArgs && pdispparams->rgvarg[0].vt == VT_DISPATCH) {
      CComQIPtr<IRibbonControl> control(pdispparams->rgvarg[0].pdispVal);
      if (control) {
        CComBSTR tag_string;
        control->get_Tag(&tag_string);
        tag = _wtoi(tag_string);
      }
    }
    return tag;

  }

  STDMETHOD(Invoke)(DISPID dispidMember, REFIID riid,
    LCID lcid, WORD wFlags, DISPPARAMS* pdispparams, VARIANT* pvarResult,
    EXCEPINFO* pexcepinfo, UINT* puArgErr)
  {
    static CComBSTR bstr;
    CComVariant result;
    int tag;

    switch (dispidMember)
    {
    case DispIds::RibbonLoaded:
      return HandleCacheRibbon(pdispparams);

    case DispIds::AddUserButton:
    {
      if (pdispparams->cArgs >= 4) {

        uint32_t id = pdispparams->rgvarg[0].intVal;
        CComBSTR image(pdispparams->rgvarg[1].bstrVal);
        CComBSTR language_tag(pdispparams->rgvarg[2].bstrVal);
        CComBSTR label(pdispparams->rgvarg[3].bstrVal);
        
        CComBSTR tip = L"";
        if (pdispparams->cArgs == 5) tip = pdispparams->rgvarg[4].bstrVal;

        UserButton button(label.m_str, language_tag.m_str, image.m_str, tip.m_str, id);
        user_buttons_.push_back(button);
        
        if (m_pRibbonUI) m_pRibbonUI->Invalidate();
        return S_OK;
      }
      return E_FAIL;
    }

    case DispIds::GetLabel:
      result = "NEVEN\u00a0Console";
      result.Detach(pvarResult);
      return S_OK;

    case DispIds::UserButtonAction:
    {
      tag = ButtonTag(pdispparams);
      CComQIPtr< Excel::_Application > pApp(m_pApplication);
      if (tag > 0 && user_buttons_.size() > tag - 1 && pApp) {
        const UserButton &button = user_buttons_[tag - 1];

        CComVariant result;
        CComVariant command = "RJ.ButtonCallback";
        CComVariant id = button.id_;
        CComVariant language = button.language_tag_.c_str();

        CComVariant missing(DISP_E_PARAMNOTFOUND, VT_ERROR);
        return pApp->_Run2(command, id, language, missing, missing, missing, missing, missing, missing, missing,
          missing, missing, missing, missing, missing, missing, missing, missing, missing, missing, missing, missing,
          missing, missing, missing, missing, missing, missing, missing, missing, missing, 1033, &result);
      }
      return E_FAIL;
    }

    case DispIds::GetUserButtonImage:
    {
      tag = ButtonTag(pdispparams);
      if (tag > 0 && user_buttons_.size() > tag - 1) {
        result = user_buttons_[tag - 1].image_mso_.c_str();
        result.Detach(pvarResult);
      }
      return S_OK;
    }
    case DispIds::GetUserButtonLabel:
      tag = ButtonTag(pdispparams);
      result = "";
      if (tag > 0 && user_buttons_.size() > tag - 1) {
        result = user_buttons_[tag - 1].label_.c_str();
      }
      result.Detach(pvarResult);
      return S_OK;

    case DispIds::GetUserButtonTip:
      tag = ButtonTag(pdispparams);
      result = "";
      if (tag > 0 && user_buttons_.size() > tag - 1) {
        result = user_buttons_[tag - 1].tip_.c_str();
      }
      result.Detach(pvarResult);
      return S_OK;

    case DispIds::GetUserButtonsVisible:
      result = (user_buttons_.size() > 0) ? VARIANT_TRUE : VARIANT_FALSE;
      result.Detach(pvarResult);
      return S_OK;

    case DispIds::GetUserButtonVisible:
      tag = ButtonTag(pdispparams);
      result = (tag > 0 && user_buttons_.size() > tag-1) ? VARIANT_TRUE : VARIANT_FALSE;
      result.Detach(pvarResult);
      return S_OK;

    case DispIds::GetImage:
    {
      if (pdispparams->cArgs > 0 && pdispparams->rgvarg[pdispparams->cArgs - 1].vt == VT_BSTR) {
          CComBSTR image_id(pdispparams->rgvarg[pdispparams->cArgs - 1].bstrVal);
          
          HDC screen = GetDC(NULL);
          double scale = GetDeviceCaps(screen, LOGPIXELSX) / 96.0;
          ReleaseDC(NULL, screen);

          if (image_id == L"logo") {
              return GetImage(scale > 1 ? IDB_LOGO_32 : IDB_LOGO_16, pvarResult);
          }
          else if (image_id == L"r_logo") {
              return GetImage(scale > 1 ? IDB_R_32 : IDB_R_16, pvarResult);
          }
          else if (image_id == L"julia_logo") {
              return GetImage(scale > 1 ? IDB_JULIA_32 : IDB_JULIA_16, pvarResult);
          }
          else if (image_id == L"quarto_logo") {
              return GetImage(scale > 1 ? IDB_QUARTO_32 : IDB_QUARTO_16, pvarResult);
          }
          else if (image_id == L"neven_logo") {
              return GetImage(scale > 1 ? IDB_NEVEN_32 : IDB_NEVEN_16, pvarResult);
          }
          // Default to console
          return GetImage(scale > 1 ? IDB_CONSOLE_32 : IDB_CONSOLE_16, pvarResult);
      }
      return E_FAIL;
    }

    case DispIds::ShowConsole:
    case DispIds::ShowRTerminal:
    {
      // Open R GUI — try common paths
      const char* r_paths[] = {
          "C:\\Program Files\\R\\R-4.4.1\\bin\\x64\\Rgui.exe",
          "C:\\Program Files\\R\\R-4.4.2\\bin\\x64\\Rgui.exe",
          "C:\\Program Files\\R\\R-4.3.3\\bin\\x64\\Rgui.exe",
          nullptr
      };
      for (int i = 0; r_paths[i]; i++) {
          if (GetFileAttributesA(r_paths[i]) != INVALID_FILE_ATTRIBUTES) {
              ShellExecuteA(NULL, "open", r_paths[i], NULL, NULL, SW_SHOWNORMAL);
              return S_OK;
          }
      }
      // Fallback: try PATH
      ShellExecuteA(NULL, "open", "Rgui.exe", NULL, NULL, SW_SHOWNORMAL);
      return S_OK;
    }

    case DispIds::ShowJuliaTerminal:
    {
      ShellExecuteA(NULL, "open", "julia.exe", NULL, NULL, SW_SHOWNORMAL);
      return S_OK;
    }

    case DispIds::ClearUserButtons:
      user_buttons_.clear();
      if (m_pRibbonUI) m_pRibbonUI->Invalidate();
      break;

    case DispIds::UpdateRibbon:
      if (m_pRibbonUI) m_pRibbonUI->Invalidate();
      break;

    // ─── New NEVEN v2.0 commands ───
    case DispIds::OnPlutoStart:
      return RunXllFunction(L"NEVEN.cmd.pluto.start");
    case DispIds::OnPlutoStop:
      return RunXllFunction(L"NEVEN.cmd.pluto.stop");
    case DispIds::OnViewDialog:
      return RunXllFunction(L"NEVEN.v.dialog");
    case DispIds::OnEditor:
      return RunXllFunction(L"NEVEN.cmd.editor");
    case DispIds::OnCloseViewers:
      return RunXllFunction(L"NEVEN.v.closeall");
    case DispIds::OnNotebookDialog:
      return RunXllFunction(L"NEVEN.notebook.dialog");
    case DispIds::OnQuartoDialog:
      return RunXllFunction(L"NEVEN.v.dialog");  // Reuse file dialog for .qmd
    case DispIds::OnRefreshFunctions:
      return RunXllFunction(L"RJ_UpdateFunctions");
    case DispIds::OnOpenScriptsDir:
    {
      ShellExecuteA(NULL, "explore", "C:\\NEVEN\\", NULL, NULL, SW_SHOWNORMAL);
      return S_OK;
    }
    case DispIds::OnOpenConfig:
    {
      ShellExecuteA(NULL, "open", "C:\\NEVEN\\neven-config.json", NULL, NULL, SW_SHOWNORMAL);
      return S_OK;
    }
    case DispIds::OnAbout:
      return RunXllFunction(L"NEVEN.about.dialog");

    case DispIds::OnOpenDocs:
    {
      // Open NEVEN documentation in WebView2 viewer
      CComQIPtr<Excel::_Application> pApp(m_pApplication);
      if (pApp) {
          CComVariant runCmd(L"NEVEN.v");
          CComVariant docPath("C:/NEVEN/neven-docs.html");
          CComVariant result;
          CComVariant missing(DISP_E_PARAMNOTFOUND, VT_ERROR);
          pApp->_Run2(runCmd, docPath, missing, missing, missing, missing, missing, missing,
                       missing, missing, missing, missing, missing, missing, missing, missing,
                       missing, missing, missing, missing, missing, missing, missing, missing,
                       missing, missing, missing, missing, missing, missing, missing, 1033, &result);
      }
      return S_OK;
    }

    case DispIds::OnViewerList:
    {
      // Show active viewers in a message box
      CComQIPtr<Excel::_Application> pApp(m_pApplication);
      if (pApp) {
          CComVariant cmd(L"NEVEN.v.list");
          CComVariant result;
          CComVariant missing(DISP_E_PARAMNOTFOUND, VT_ERROR);
          pApp->_Run2(cmd, missing, missing, missing, missing, missing, missing, missing,
                       missing, missing, missing, missing, missing, missing, missing, missing,
                       missing, missing, missing, missing, missing, missing, missing, missing,
                       missing, missing, missing, missing, missing, missing, missing, 1033, &result);
          if (result.vt == VT_BSTR) {
              char buf[1024];
              WideCharToMultiByte(CP_UTF8, 0, result.bstrVal, -1, buf, sizeof(buf), NULL, NULL);
              MessageBoxA(NULL, buf, "NEVEN - Visores Activos", MB_OK | MB_ICONINFORMATION);
          }
      }
      return S_OK;
    }

    case DispIds::OnInstallPkgR:
    {
      CComQIPtr<Excel::_Application> pApp(m_pApplication);
      if (pApp) {
          // Step 1: Ask which language
          CComBSTR langMacro(L"INPUT(\"Seleccione lenguaje: 1=R, 2=Julia, 3=Python\",1,\"Instalar Paquetes\",\"1\")");
          CComVariant langResult;
          pApp->ExecuteExcel4Macro(langMacro, 1033, &langResult);
          
          int lang = 1; // default R
          if (langResult.vt == VT_R8) lang = (int)langResult.dblVal;
          else if (langResult.vt == VT_BSTR && SysStringLen(langResult.bstrVal) > 0) {
              char buf[8];
              WideCharToMultiByte(CP_UTF8, 0, langResult.bstrVal, -1, buf, sizeof(buf), NULL, NULL);
              lang = atoi(buf);
          }
          if (lang < 1 || lang > 3) return S_OK; // cancelled

          // Step 2: Ask package name
          const wchar_t* prompts[] = {
              L"INPUT(\"Paquete(s) R a instalar (ej: ggplot2, dplyr):\",2,\"Instalar Paquete R\",\"\")",
              L"INPUT(\"Paquete(s) Julia a instalar (ej: Plots, DataFrames):\",2,\"Instalar Paquete Julia\",\"\")",
              L"INPUT(\"Paquete(s) Python a instalar (ej: numpy, pandas):\",2,\"Instalar Paquete Python\",\"\")"
          };
          CComBSTR pkgMacro(prompts[lang - 1]);
          CComVariant pkgResult;
          pApp->ExecuteExcel4Macro(pkgMacro, 1033, &pkgResult);
          
          if (pkgResult.vt != VT_BSTR || SysStringLen(pkgResult.bstrVal) == 0) return S_OK; // cancelled
          
          char pkg[512];
          WideCharToMultiByte(CP_UTF8, 0, pkgResult.bstrVal, -1, pkg, sizeof(pkg), NULL, NULL);
          
          std::string cmd;
          CComVariant runCmd;
          const char* langName;
          
          switch (lang) {
          case 1: // R
              cmd = std::string("install.packages(c('") + pkg + "'), repos='https://cran.r-project.org', quiet=TRUE)";
              runCmd = L"NEVEN.r";
              langName = "R";
              break;
          case 2: // Julia
              cmd = std::string("import Pkg; Pkg.add(\"") + pkg + "\")";
              runCmd = L"NEVEN.j";
              langName = "Julia";
              break;
          case 3: // Python
              cmd = std::string("import subprocess; subprocess.run(['pip', 'install', '") + pkg + "'])";
              runCmd = L"NEVEN.P";
              langName = "Python";
              break;
          }
          
          CComVariant cmdArg(cmd.c_str());
          CComVariant result;
          CComVariant missing(DISP_E_PARAMNOTFOUND, VT_ERROR);
          pApp->_Run2(runCmd, cmdArg, missing, missing, missing, missing, missing, missing,
                       missing, missing, missing, missing, missing, missing, missing, missing,
                       missing, missing, missing, missing, missing, missing, missing, missing,
                       missing, missing, missing, missing, missing, missing, missing, 1033, &result);
          MessageBoxA(NULL, (std::string("Paquete(s) '") + pkg + "' - instalacion iniciada en " + langName + ".").c_str(),
                      "NEVEN", MB_OK | MB_ICONINFORMATION);
      }
      return S_OK;
    }

    case DispIds::OnInstallPkgJulia:
    {
      CComQIPtr<Excel::_Application> pApp(m_pApplication);
      if (pApp) {
          CComBSTR macro(L"INPUT(\"Nombre del paquete Julia a instalar (ej: Plots):\",2,\"Instalar Paquete Julia\",\"\")");
          CComVariant cvResult;
          pApp->ExecuteExcel4Macro(macro, 1033, &cvResult);
          if (cvResult.vt == VT_BSTR && SysStringLen(cvResult.bstrVal) > 0) {
              char pkg[256];
              WideCharToMultiByte(CP_UTF8, 0, cvResult.bstrVal, -1, pkg, sizeof(pkg), NULL, NULL);
              std::string jCmd = std::string("import Pkg; Pkg.add(\"") + pkg + "\")";
              CComVariant runCmd(L"NEVEN.j");
              CComVariant jArg(jCmd.c_str());
              CComVariant result;
              CComVariant missing(DISP_E_PARAMNOTFOUND, VT_ERROR);
              pApp->_Run2(runCmd, jArg, missing, missing, missing, missing, missing, missing,
                           missing, missing, missing, missing, missing, missing, missing, missing,
                           missing, missing, missing, missing, missing, missing, missing, missing,
                           missing, missing, missing, missing, missing, missing, missing, 1033, &result);
              MessageBoxA(NULL, (std::string("Paquete '") + pkg + "' - instalacion iniciada en Julia.").c_str(),
                          "NEVEN", MB_OK | MB_ICONINFORMATION);
          }
      }
      return S_OK;
    }

    case DispIds::OnListPkgR:
    {
      CComQIPtr<Excel::_Application> pApp(m_pApplication);
      if (pApp) {
          CComVariant runCmd(L"NEVEN.r");
          CComVariant rArg("paste(sort(rownames(installed.packages())), collapse=', ')");
          CComVariant result;
          CComVariant missing(DISP_E_PARAMNOTFOUND, VT_ERROR);
          pApp->_Run2(runCmd, rArg, missing, missing, missing, missing, missing, missing,
                       missing, missing, missing, missing, missing, missing, missing, missing,
                       missing, missing, missing, missing, missing, missing, missing, missing,
                       missing, missing, missing, missing, missing, missing, missing, 1033, &result);
          if (result.vt == VT_BSTR) {
              char buf[8192];
              WideCharToMultiByte(CP_UTF8, 0, result.bstrVal, -1, buf, sizeof(buf), NULL, NULL);
              MessageBoxA(NULL, buf, "NEVEN - Paquetes R Instalados", MB_OK | MB_ICONINFORMATION);
          }
      }
      return S_OK;
    }

    case DispIds::OnListPkgJulia:
    {
      CComQIPtr<Excel::_Application> pApp(m_pApplication);
      if (pApp) {
          CComVariant runCmd(L"NEVEN.j");
          CComVariant jArg("import Pkg; join(sort(collect(keys(Pkg.project().dependencies))), \", \")");
          CComVariant result;
          CComVariant missing(DISP_E_PARAMNOTFOUND, VT_ERROR);
          pApp->_Run2(runCmd, jArg, missing, missing, missing, missing, missing, missing,
                       missing, missing, missing, missing, missing, missing, missing, missing,
                       missing, missing, missing, missing, missing, missing, missing, missing,
                       missing, missing, missing, missing, missing, missing, missing, 1033, &result);
          if (result.vt == VT_BSTR) {
              char buf[8192];
              WideCharToMultiByte(CP_UTF8, 0, result.bstrVal, -1, buf, sizeof(buf), NULL, NULL);
              MessageBoxA(NULL, buf, "NEVEN - Paquetes Julia Instalados", MB_OK | MB_ICONINFORMATION);
          }
      }
      return S_OK;
    }

    }

    return RIBBON_INTERFACE::Invoke(dispidMember, riid, lcid, wFlags, pdispparams, pvarResult, pexcepinfo, puArgErr);
  }

  // Local Methods

  int SetPointers(ULONG_PTR excel_pointer, ULONG_PTR ribbon_pointer)
  {
    HANDLE handle = GetCurrentProcess();
    HMODULE module_handles[1024];
    DWORD bytes;
    char buffer[MAX_PATH];

    if (EnumProcessModules(handle, module_handles, sizeof(module_handles), &bytes))
    {
      int count = bytes / sizeof(HANDLE);
      for (int i = 0; i < count; i++)
      {
        if (GetModuleFileNameExA(handle, module_handles[i], buffer, MAX_PATH))
        {
          std::string module_name(buffer);
          if (std::string::npos != module_name.find("NEVEN") && std::string::npos != module_name.find(".xll"))
          {
            auto procedure = GetProcAddress(module_handles[i], "RJ_SetPointers");
            if (procedure) {
              SetPointersProcedure set_pointers = reinterpret_cast<SetPointersProcedure>(procedure);
              set_pointers(excel_pointer, ribbon_pointer);
              return 0;
            }
          }
        }
      }
    }

    return -1;
  }

  HRESULT HandleCacheRibbon(DISPPARAMS* pdispparams)
  {
    if (pdispparams->cArgs > 0
      && pdispparams->rgvarg[0].vt == VT_DISPATCH)
    {
      m_pRibbonUI = pdispparams->rgvarg[0].pdispVal;
      return S_OK;
    }
    return E_FAIL;
  }

  HRESULT HandleControlInvocation(const char *szCmd)
  {
    CComQIPtr< Excel::_Application > pApp(m_pApplication);
    if (pApp)
    {
      CComBSTR bstrCmd(szCmd);
      CComVariant cvRslt;
      HRESULT hr = pApp->ExecuteExcel4Macro(bstrCmd, 1033, &cvRslt);
    }
    return S_OK;
  }

  HRESULT RunXllFunction(const wchar_t* functionName)
  {
    CComQIPtr< Excel::_Application > pApp(m_pApplication);
    if (pApp)
    {
      CComVariant command(functionName);
      CComVariant result;
      CComVariant missing(DISP_E_PARAMNOTFOUND, VT_ERROR);
      pApp->_Run2(command, missing, missing, missing, missing, missing, missing, missing,
                   missing, missing, missing, missing, missing, missing, missing, missing,
                   missing, missing, missing, missing, missing, missing, missing, missing,
                   missing, missing, missing, missing, missing, missing, missing, 1033, &result);
    }
    return S_OK;
  }

};

OBJECT_ENTRY_AUTO(__uuidof(Connect), CConnect)
