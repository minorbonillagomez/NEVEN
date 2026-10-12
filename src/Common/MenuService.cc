/**
 * Copyright (c) 2026 RJ2XCL Project — GPL v3
 *
 * @file MenuService.cc
 * @brief CommandBar toolbar for RJ2XCL in Excel with grouped buttons.
 */

#include "MenuService.h"
#include "LogService.h"

#include <oleacc.h>
#include <atlbase.h>
#include <atlcom.h>

#pragma comment(lib, "oleacc.lib")

namespace rj2xcl {

bool MenuService::menu_created_ = false;
Language MenuService::current_language_ = Language::ES;

// ═══════════════════════════════════════════════════════════════════════════
// Button definitions — ES/EN
// ═══════════════════════════════════════════════════════════════════════════

struct BtnDef {
    const wchar_t* es;
    const wchar_t* en;
    const wchar_t* action;
    int faceId;
    bool sep;  // separator before
};

static BtnDef BUTTONS[] = {
    // ─── Visualizacion ───
    { L"Abrir HTML",             L"Open HTML",           L"RJ2XCL.VIEW.DIALOG",        1017, false },
    { L"Editor Presentaciones",  L"Presentation Editor", L"RJ2XCL.CMD.EDITOR",          987, false },
    // ─── Pluto.jl ───
    { L"Iniciar Pluto",          L"Start Pluto",         L"RJ2XCL.CMD.PLUTO.START",     558, true },
    { L"Notebooks",              L"Notebooks",           L"RJ2XCL.NOTEBOOK.DIALOG",      23, false },
    { L"Detener Pluto",          L"Stop Pluto",          L"RJ2XCL.CMD.PLUTO.STOP",      353, false },
    // ─── Info ───
    { L"Acerca de",              L"About",               L"RJ2XCL.ABOUT.DIALOG",        487, true },
};
static constexpr int BTN_COUNT = 6;

// ═══════════════════════════════════════════════════════════════════════════
// COM Helpers (minimal)
// ═══════════════════════════════════════════════════════════════════════════

static IDispatch* GetExcelApp() {
    HWND h = FindWindowA("XLMAIN", nullptr);
    if (!h) return nullptr;
    HWND d = FindWindowExA(h, nullptr, "XLDESK", nullptr);
    if (!d) return nullptr;
    HWND e = FindWindowExA(d, nullptr, "EXCEL7", nullptr);
    if (!e) return nullptr;

    IDispatch* p = nullptr;
    if (FAILED(AccessibleObjectFromWindow(e, (DWORD)OBJID_NATIVEOM, IID_IDispatch, (void**)&p)) || !p)
        return nullptr;

    DISPID id; OLECHAR* n = L"Application";
    if (FAILED(p->GetIDsOfNames(IID_NULL, &n, 1, LOCALE_USER_DEFAULT, &id))) { p->Release(); return nullptr; }
    DISPPARAMS dp = {}; CComVariant r;
    p->Invoke(id, IID_NULL, LOCALE_USER_DEFAULT, DISPATCH_PROPERTYGET, &dp, &r, nullptr, nullptr);
    p->Release();
    if (r.vt != VT_DISPATCH || !r.pdispVal) return nullptr;
    r.pdispVal->AddRef();
    return r.pdispVal;
}

static HRESULT DGet(IDispatch* p, const wchar_t* n, CComVariant* r) {
    DISPID id; OLECHAR* w = const_cast<OLECHAR*>(n);
    HRESULT hr = p->GetIDsOfNames(IID_NULL, &w, 1, LOCALE_USER_DEFAULT, &id);
    if (FAILED(hr)) return hr;
    DISPPARAMS dp = {};
    return p->Invoke(id, IID_NULL, LOCALE_USER_DEFAULT, DISPATCH_PROPERTYGET, &dp, r, nullptr, nullptr);
}

static HRESULT DPut(IDispatch* p, const wchar_t* n, CComVariant& v) {
    DISPID id; OLECHAR* w = const_cast<OLECHAR*>(n);
    HRESULT hr = p->GetIDsOfNames(IID_NULL, &w, 1, LOCALE_USER_DEFAULT, &id);
    if (FAILED(hr)) return hr;
    DISPID pid = DISPID_PROPERTYPUT;
    DISPPARAMS dp = {}; dp.cArgs = 1; dp.rgvarg = &v; dp.cNamedArgs = 1; dp.rgdispidNamedArgs = &pid;
    return p->Invoke(id, IID_NULL, LOCALE_USER_DEFAULT, DISPATCH_PROPERTYPUT, &dp, nullptr, nullptr, nullptr);
}

static HRESULT DCall(IDispatch* p, const wchar_t* n, CComVariant* a, int na, CComVariant* r) {
    DISPID id; OLECHAR* w = const_cast<OLECHAR*>(n);
    HRESULT hr = p->GetIDsOfNames(IID_NULL, &w, 1, LOCALE_USER_DEFAULT, &id);
    if (FAILED(hr)) return hr;
    DISPPARAMS dp = {}; dp.cArgs = na; dp.rgvarg = a;
    return p->Invoke(id, IID_NULL, LOCALE_USER_DEFAULT, DISPATCH_METHOD, &dp, r, nullptr, nullptr);
}

// ═══════════════════════════════════════════════════════════════════════════
// Public API
// ═══════════════════════════════════════════════════════════════════════════

bool MenuService::CreateMenu() {
    if (menu_created_) return true;

    IDispatch* pApp = GetExcelApp();
    if (!pApp) { RJ2XCL_LOG_WARN("MenuService: no Excel App"); return false; }

    CComVariant vBars;
    if (FAILED(DGet(pApp, L"CommandBars", &vBars)) || vBars.vt != VT_DISPATCH) {
        pApp->Release(); return false;
    }

    // CommandBars.Add("RJ2XCL", msoBarTop, false, true)
    DISPID addId; OLECHAR* addN = L"Add";
    if (FAILED(vBars.pdispVal->GetIDsOfNames(IID_NULL, &addN, 1, LOCALE_USER_DEFAULT, &addId))) {
        vBars.pdispVal->Release(); pApp->Release(); return false;
    }

    CComVariant args[4];
    args[3] = CComVariant(L"RJ2XCL"); args[2] = CComVariant(1L);
    args[1] = CComVariant(false);      args[0] = CComVariant(true);
    DISPPARAMS dp = {}; dp.cArgs = 4; dp.rgvarg = args;

    CComVariant vBar;
    if (FAILED(vBars.pdispVal->Invoke(addId, IID_NULL, LOCALE_USER_DEFAULT,
                                       DISPATCH_METHOD, &dp, &vBar, nullptr, nullptr))
        || vBar.vt != VT_DISPATCH) {
        vBars.pdispVal->Release(); pApp->Release(); return false;
    }

    CComVariant vVis(true); DPut(vBar.pdispVal, L"Visible", vVis);

    CComVariant vCtls;
    DGet(vBar.pdispVal, L"Controls", &vCtls);
    if (vCtls.vt != VT_DISPATCH) {
        vBar.pdispVal->Release(); vBars.pdispVal->Release(); pApp->Release();
        return false;
    }
    IDispatch* pCtls = vCtls.pdispVal;

    bool es = (current_language_ == Language::ES);

    for (int i = 0; i < BTN_COUNT; i++) {
        CComVariant vType(1L); // msoControlButton
        CComVariant vBtn;
        if (FAILED(DCall(pCtls, L"Add", &vType, 1, &vBtn)) || vBtn.vt != VT_DISPATCH) continue;

        IDispatch* pB = vBtn.pdispVal;
        CComVariant vCap(es ? BUTTONS[i].es : BUTTONS[i].en);  DPut(pB, L"Caption", vCap);
        CComVariant vAct(BUTTONS[i].action);                     DPut(pB, L"OnAction", vAct);
        CComVariant vSty(3L);                                    DPut(pB, L"Style", vSty);
        if (BUTTONS[i].faceId > 0) { CComVariant vF((long)BUTTONS[i].faceId); DPut(pB, L"FaceId", vF); }
        if (BUTTONS[i].sep)        { CComVariant vS(true); DPut(pB, L"BeginGroup", vS); }
        pB->Release();
    }

    pCtls->Release();
    vBar.pdispVal->Release();
    vBars.pdispVal->Release();
    pApp->Release();

    menu_created_ = true;
    RJ2XCL_LOG_INFO("MenuService: toolbar created (%s)", es ? "ES" : "EN");
    return true;
}

void MenuService::RemoveMenu() {
    if (!menu_created_) return;
    IDispatch* pApp = GetExcelApp();
    if (!pApp) return;

    CComVariant vBars;
    if (SUCCEEDED(DGet(pApp, L"CommandBars", &vBars)) && vBars.vt == VT_DISPATCH) {
        CComVariant vN(L"RJ2XCL"), vB;
        if (SUCCEEDED(DCall(vBars.pdispVal, L"Item", &vN, 1, &vB)) && vB.vt == VT_DISPATCH) {
            DCall(vB.pdispVal, L"Delete", nullptr, 0, nullptr);
            vB.pdispVal->Release();
        }
        vBars.pdispVal->Release();
    }
    pApp->Release();
    menu_created_ = false;
}

void MenuService::ToggleLanguage() {
    current_language_ = (current_language_ == Language::ES) ? Language::EN : Language::ES;
    RJ2XCL_LOG_INFO("MenuService: toggled to %s", current_language_ == Language::ES ? "ES" : "EN");
    RemoveMenu();
    CreateMenu();
}

Language MenuService::GetLanguage() { return current_language_; }

} // namespace rj2xcl
