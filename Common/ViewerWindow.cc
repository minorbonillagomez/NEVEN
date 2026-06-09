/**
 * Copyright (c) 2026 RJ2XCL Project — GPL v3
 *
 * @file ViewerWindow.cc
 * @brief Implementation of the Win32 + WebView2 viewer window.
 */

#include "ViewerWindow.h"
#include "PostMessageBridge.h"
#include "LogService.h"
#include "json11/json11.hpp"

#include <WebView2.h>
#include <wrl.h>
#include <sstream>
#include <shlwapi.h>

using Microsoft::WRL::Callback;

namespace rj2xcl {

// ─── Static Members ─────────────────────────────────────────────────────

bool ViewerWindow::window_class_registered_ = false;
const wchar_t* ViewerWindow::WINDOW_CLASS_NAME = L"RJ2XCL_ViewerWindow";

// ─── Window Class Registration ──────────────────────────────────────────

bool ViewerWindow::RegisterWindowClass() {
    if (window_class_registered_) return true;

    WNDCLASSEXW wc = {};
    wc.cbSize = sizeof(WNDCLASSEXW);
    wc.lpfnWndProc = ViewerWindow::WindowProc;
    wc.hInstance = GetModuleHandle(nullptr);
    wc.hCursor = LoadCursor(nullptr, IDC_ARROW);
    wc.hbrBackground = (HBRUSH)(COLOR_WINDOW + 1);
    wc.lpszClassName = WINDOW_CLASS_NAME;

    if (!RegisterClassExW(&wc)) {
        DWORD err = GetLastError();
        if (err != ERROR_CLASS_ALREADY_EXISTS) {
            RJ2XCL_LOG_ERR("ViewerWindow: RegisterClassEx failed: %d", err);
            return false;
        }
    }

    window_class_registered_ = true;
    return true;
}

// ─── Constructor / Destructor ───────────────────────────────────────────

ViewerWindow::ViewerWindow(HWND parent_hwnd,
                           ICoreWebView2Environment* environment,
                           const std::string& viewer_id,
                           const std::string& title,
                           int width, int height)
    : hwnd_(nullptr)
    , parent_hwnd_(parent_hwnd)
    , environment_(environment)
    , controller_(nullptr)
    , webview_(nullptr)
    , viewer_id_(viewer_id)
    , title_(title)
{
    if (!RegisterWindowClass()) return;

    // Build window title: "NEVEN - [Title]"
    std::wstring wide_title;
    int wlen = MultiByteToWideChar(CP_UTF8, 0, title.c_str(), -1, nullptr, 0);
    wide_title.resize(wlen);
    MultiByteToWideChar(CP_UTF8, 0, title.c_str(), -1, &wide_title[0], wlen);

    // Position: right half of the screen (snap-right layout)
    // Also snap Excel to the left half for side-by-side view
    RECT work_area;
    SystemParametersInfo(SPI_GETWORKAREA, 0, &work_area, 0);
    int work_w = work_area.right - work_area.left;
    int work_h = work_area.bottom - work_area.top;

    // Snap Excel to left half
    HWND excel_hwnd = FindWindowW(L"XLMAIN", nullptr);
    if (excel_hwnd) {
        SetWindowPos(excel_hwnd, nullptr,
                     work_area.left, work_area.top,
                     work_w / 2, work_h,
                     SWP_NOZORDER | SWP_NOACTIVATE);
    }

    // Snap viewer to right half
    int x = work_area.left + work_w / 2;
    int y = work_area.top;
    width = work_w / 2;
    height = work_h;

    // Create modeless window — WS_EX_APPWINDOW for taskbar + Alt+Tab visibility
    hwnd_ = CreateWindowExW(
        WS_EX_APPWINDOW,           // Visible in taskbar and Alt+Tab
        WINDOW_CLASS_NAME,
        wide_title.c_str(),
        WS_OVERLAPPEDWINDOW,       // Standard resizable window
        x, y, width, height,
        nullptr,                    // No owner (independent top-level window)
        nullptr,                    // No menu
        GetModuleHandle(nullptr),
        this                        // Pass this pointer for WM_CREATE
    );

    if (!hwnd_) {
        RJ2XCL_LOG_ERR("ViewerWindow: CreateWindowEx failed: %d", GetLastError());
        return;
    }

    // Store this pointer for WindowProc
    SetWindowLongPtr(hwnd_, GWLP_USERDATA, reinterpret_cast<LONG_PTR>(this));

    // Create WebView2 controller
    CreateWebView();
}

ViewerWindow::~ViewerWindow() {
    if (controller_) {
        controller_->Close();
        controller_->Release();
        controller_ = nullptr;
    }
    if (webview_) {
        webview_->Release();
        webview_ = nullptr;
    }
    if (hwnd_) {
        DestroyWindow(hwnd_);
        hwnd_ = nullptr;
    }
}

// ─── WebView2 Setup ─────────────────────────────────────────────────────

void ViewerWindow::CreateWebView() {
    if (!environment_ || !hwnd_) return;

    environment_->CreateCoreWebView2Controller(
        hwnd_,
        Callback<ICoreWebView2CreateCoreWebView2ControllerCompletedHandler>(
            [this](HRESULT result, ICoreWebView2Controller* controller) -> HRESULT {
                if (FAILED(result) || !controller) {
                    RJ2XCL_LOG_ERR("ViewerWindow: CreateController failed: 0x%08X", result);
                    return S_OK;
                }

                controller_ = controller;
                controller_->AddRef();

                // Set dark background color (grafito #2D2D2D)
                ICoreWebView2Controller2* controller2 = nullptr;
                if (SUCCEEDED(controller_->QueryInterface(IID_PPV_ARGS(&controller2)))) {
                    COREWEBVIEW2_COLOR bgColor = { 255, 45, 45, 45 }; // ARGB: opaque #2D2D2D
                    controller2->put_DefaultBackgroundColor(bgColor);
                    controller2->Release();
                }

                // Get the webview interface
                controller_->get_CoreWebView2(&webview_);

                // Resize to fill the window
                RECT bounds;
                GetClientRect(hwnd_, &bounds);
                controller_->put_Bounds(bounds);
                controller_->put_IsVisible(TRUE);

                // Inject JavaScript bridge
                InjectBridgeScript();

                // Navigate to pending content (if any)
                if (!pending_url_.empty()) {
                    NavigateToUrl(pending_url_);
                    pending_url_.clear();
                } else if (!pending_html_.empty()) {
                    NavigateToString(pending_html_);
                    pending_html_.clear();
                }

                // Register web message handler
                if (webview_ && web_message_callback_) {
                    webview_->add_WebMessageReceived(
                        Callback<ICoreWebView2WebMessageReceivedEventHandler>(
                            [this](ICoreWebView2* sender,
                                   ICoreWebView2WebMessageReceivedEventArgs* args) -> HRESULT {
                                LPWSTR message = nullptr;
                                args->TryGetWebMessageAsString(&message);
                                if (message) {
                                    // Convert wide to UTF-8
                                    int len = WideCharToMultiByte(CP_UTF8, 0, message, -1, nullptr, 0, nullptr, nullptr);
                                    if (len > 1) {
                                        std::string utf8(len - 1, 0); // -1 to exclude null terminator
                                        WideCharToMultiByte(CP_UTF8, 0, message, -1, &utf8[0], len, nullptr, nullptr);
                                        CoTaskMemFree(message);

                                        if (web_message_callback_) {
                                            web_message_callback_(viewer_id_, utf8);
                                        }
                                    } else {
                                        CoTaskMemFree(message);
                                    }
                                }
                                return S_OK;
                            }).Get(), nullptr);
                }

                RJ2XCL_LOG_INFO("ViewerWindow: WebView2 controller created for %s", viewer_id_.c_str());
                return S_OK;
            }).Get());
}

void ViewerWindow::InjectBridgeScript() {
    if (!webview_) return;

    // Inject the PostMessage bridge script
    const char* script = PostMessageBridge::GetBridgeScript();
    int wlen = MultiByteToWideChar(CP_UTF8, 0, script, -1, nullptr, 0);
    std::wstring wide_script(wlen, 0);
    MultiByteToWideChar(CP_UTF8, 0, script, -1, &wide_script[0], wlen);

    webview_->AddScriptToExecuteOnDocumentCreated(wide_script.c_str(), nullptr);

    // Inject the floating Save Button script
    // Uses DOMContentLoaded to ensure document.body exists
    // Uses Unicode escapes for emoji compatibility with MSVC
    const char* save_btn_script = R"(
(function() {
    function injectSaveBtn() {
        if (document.getElementById('neven-save-btn')) return;
        if (!document.body) { setTimeout(injectSaveBtn, 100); return; }
        var btn = document.createElement('div');
        btn.id = 'neven-save-btn';
        btn.innerHTML = '&#x1F4BE;';
        btn.title = 'Guardar';
        btn.style.cssText = 'position:fixed;bottom:20px;right:20px;width:44px;height:44px;border-radius:50%;background:rgba(45,45,45,0.7);color:#a0e515;font-size:22px;display:flex;align-items:center;justify-content:center;cursor:pointer;z-index:99999;transition:opacity 0.2s;opacity:0.5;user-select:none;';
        btn.onmouseenter = function() { btn.style.opacity = '1'; };
        btn.onmouseleave = function() { btn.style.opacity = '0.5'; };
        btn.onclick = function() { btn.innerHTML = '&#x23F3;'; window.chrome.webview.postMessage(JSON.stringify({action:'save-request'})); setTimeout(function(){btn.innerHTML='&#x1F4BE;';},2000); };
        document.body.appendChild(btn);
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', injectSaveBtn);
    } else {
        injectSaveBtn();
    }
})();
)";
    int wlen2 = MultiByteToWideChar(CP_UTF8, 0, save_btn_script, -1, nullptr, 0);
    std::wstring wide_save_script(wlen2, 0);
    MultiByteToWideChar(CP_UTF8, 0, save_btn_script, -1, &wide_save_script[0], wlen2);

    webview_->AddScriptToExecuteOnDocumentCreated(wide_save_script.c_str(), nullptr);
}

// ─── Navigation ─────────────────────────────────────────────────────────

HRESULT ViewerWindow::NavigateToString(const std::string& html) {
    current_html_ = html;

    if (!webview_) {
        // Controller not ready yet — store for later
        pending_html_ = html;
        pending_url_.clear();
        return S_OK;
    }

    int wlen = MultiByteToWideChar(CP_UTF8, 0, html.c_str(), -1, nullptr, 0);
    std::wstring wide_html(wlen, 0);
    MultiByteToWideChar(CP_UTF8, 0, html.c_str(), -1, &wide_html[0], wlen);

    return webview_->NavigateToString(wide_html.c_str());
}

HRESULT ViewerWindow::NavigateToFile(const std::string& file_path) {
    if (!webview_) {
        pending_url_ = "file:///" + file_path;
        pending_html_.clear();
        return S_OK;
    }

    std::string uri = "file:///" + file_path;
    // Replace backslashes with forward slashes for URI
    for (auto& c : uri) {
        if (c == '\\') c = '/';
    }

    int wlen = MultiByteToWideChar(CP_UTF8, 0, uri.c_str(), -1, nullptr, 0);
    std::wstring wide_uri(wlen, 0);
    MultiByteToWideChar(CP_UTF8, 0, uri.c_str(), -1, &wide_uri[0], wlen);

    return webview_->Navigate(wide_uri.c_str());
}

HRESULT ViewerWindow::NavigateToUrl(const std::string& url) {
    if (!webview_) {
        pending_url_ = url;
        pending_html_.clear();
        return S_OK;
    }

    int wlen = MultiByteToWideChar(CP_UTF8, 0, url.c_str(), -1, nullptr, 0);
    std::wstring wide_url(wlen, 0);
    MultiByteToWideChar(CP_UTF8, 0, url.c_str(), -1, &wide_url[0], wlen);

    return webview_->Navigate(wide_url.c_str());
}

HRESULT ViewerWindow::Reload() {
    if (!webview_) return E_FAIL;
    return webview_->Reload();
}

// ─── Communication ──────────────────────────────────────────────────────

HRESULT ViewerWindow::PostWebMessage(const std::string& json) {
    if (!webview_) return E_FAIL;

    int wlen = MultiByteToWideChar(CP_UTF8, 0, json.c_str(), -1, nullptr, 0);
    std::wstring wide_json(wlen, 0);
    MultiByteToWideChar(CP_UTF8, 0, json.c_str(), -1, &wide_json[0], wlen);

    return webview_->PostWebMessageAsJson(wide_json.c_str());
}

// ─── Window Management ──────────────────────────────────────────────────

void ViewerWindow::Show() {
    if (hwnd_) ShowWindow(hwnd_, SW_SHOW);
}

void ViewerWindow::Hide() {
    if (hwnd_) ShowWindow(hwnd_, SW_HIDE);
}

void ViewerWindow::Resize(int width, int height) {
    if (hwnd_) {
        SetWindowPos(hwnd_, nullptr, 0, 0, width, height, SWP_NOMOVE | SWP_NOZORDER);
    }
}

void ViewerWindow::SetTitle(const std::string& title) {
    title_ = title;
    if (hwnd_) {
        int wlen = MultiByteToWideChar(CP_UTF8, 0, title.c_str(), -1, nullptr, 0);
        std::wstring wide_title(wlen, 0);
        MultiByteToWideChar(CP_UTF8, 0, title.c_str(), -1, &wide_title[0], wlen);
        SetWindowTextW(hwnd_, wide_title.c_str());
    }
}

HWND ViewerWindow::GetHwnd() const { return hwnd_; }
std::string ViewerWindow::GetViewerId() const { return viewer_id_; }
std::string ViewerWindow::GetCurrentContent() const { return current_html_; }

// ─── Content Hash ───────────────────────────────────────────────────────

size_t ViewerWindow::GetContentHash() const { return content_hash_; }
void ViewerWindow::SetContentHash(size_t hash) { content_hash_ = hash; }

// ─── Scroll Preservation ────────────────────────────────────────────────

void ViewerWindow::SaveScrollPosition() {
    if (!webview_) return;

    const wchar_t* script = L"JSON.stringify({x: window.scrollX, y: window.scrollY})";
    webview_->ExecuteScript(script,
        Callback<ICoreWebView2ExecuteScriptCompletedHandler>(
            [this](HRESULT hr, LPCWSTR result) -> HRESULT {
                if (SUCCEEDED(hr) && result) {
                    // Result is a JSON-encoded string like "\"{ x: 0, y: 100 }\""
                    int len = WideCharToMultiByte(CP_UTF8, 0, result, -1, nullptr, 0, nullptr, nullptr);
                    if (len > 1) {
                        std::string utf8(len - 1, 0);
                        WideCharToMultiByte(CP_UTF8, 0, result, -1, &utf8[0], len, nullptr, nullptr);
                        // Parse simple JSON {x:N, y:N}
                        // The result from ExecuteScript is JSON-encoded, so it's a quoted string
                        // We need to parse the inner JSON
                        std::string err;
                        auto json = json11::Json::parse(utf8, err);
                        if (err.empty()) {
                            // json might be a string (double-encoded) or object
                            if (json.is_string()) {
                                auto inner = json11::Json::parse(json.string_value(), err);
                                if (err.empty()) {
                                    saved_scroll_x_ = static_cast<int>(inner["x"].number_value());
                                    saved_scroll_y_ = static_cast<int>(inner["y"].number_value());
                                }
                            } else if (json.is_object()) {
                                saved_scroll_x_ = static_cast<int>(json["x"].number_value());
                                saved_scroll_y_ = static_cast<int>(json["y"].number_value());
                            }
                        }
                    }
                }
                return S_OK;
            }).Get());
}

void ViewerWindow::RestoreScrollPosition() {
    if (!webview_) return;
    if (saved_scroll_x_ == 0 && saved_scroll_y_ == 0) return;

    std::wstring script = L"window.scrollTo(" +
        std::to_wstring(saved_scroll_x_) + L", " +
        std::to_wstring(saved_scroll_y_) + L")";
    webview_->ExecuteScript(script.c_str(), nullptr);
}

// ─── Save Operations ────────────────────────────────────────────────────

void ViewerWindow::GetPageSource(std::function<void(const std::string&)> callback) {
    if (!webview_ || !callback) return;

    const wchar_t* script = L"document.documentElement.outerHTML";
    webview_->ExecuteScript(script,
        Callback<ICoreWebView2ExecuteScriptCompletedHandler>(
            [callback](HRESULT hr, LPCWSTR result) -> HRESULT {
                if (SUCCEEDED(hr) && result) {
                    int len = WideCharToMultiByte(CP_UTF8, 0, result, -1, nullptr, 0, nullptr, nullptr);
                    if (len > 1) {
                        std::string utf8(len - 1, 0);
                        WideCharToMultiByte(CP_UTF8, 0, result, -1, &utf8[0], len, nullptr, nullptr);
                        // ExecuteScript returns JSON-encoded result, so the HTML is in a quoted string
                        std::string err;
                        auto json = json11::Json::parse(utf8, err);
                        if (err.empty() && json.is_string()) {
                            callback(json.string_value());
                        } else {
                            callback(utf8);
                        }
                    }
                }
                return S_OK;
            }).Get());
}

void ViewerWindow::CaptureAsPng(const std::string& file_path,
                                  std::function<void(HRESULT)> callback) {
    if (!webview_ || !callback) return;

    // Convert path to wide string
    int wlen = MultiByteToWideChar(CP_UTF8, 0, file_path.c_str(), -1, nullptr, 0);
    std::wstring wide_path(wlen, 0);
    MultiByteToWideChar(CP_UTF8, 0, file_path.c_str(), -1, &wide_path[0], wlen);

    // Create output stream
    IStream* stream = nullptr;
    HRESULT hr = SHCreateStreamOnFileEx(wide_path.c_str(),
        STGM_CREATE | STGM_WRITE, FILE_ATTRIBUTE_NORMAL, TRUE, nullptr, &stream);

    if (FAILED(hr) || !stream) {
        callback(hr);
        return;
    }

    webview_->CapturePreview(
        COREWEBVIEW2_CAPTURE_PREVIEW_IMAGE_FORMAT_PNG,
        stream,
        Callback<ICoreWebView2CapturePreviewCompletedHandler>(
            [callback, stream](HRESULT result) -> HRESULT {
                stream->Release();
                callback(result);
                return S_OK;
            }).Get());
}

void ViewerWindow::PrintToPdf(const std::string& file_path,
                                std::function<void(HRESULT)> callback) {
    if (!webview_ || !callback) return;

    // Query ICoreWebView2_7 for PrintToPdf
    ICoreWebView2_7* webview7 = nullptr;
    HRESULT hr = webview_->QueryInterface(IID_PPV_ARGS(&webview7));
    if (FAILED(hr) || !webview7) {
        callback(hr);
        return;
    }

    // Convert path to wide string
    int wlen = MultiByteToWideChar(CP_UTF8, 0, file_path.c_str(), -1, nullptr, 0);
    std::wstring wide_path(wlen, 0);
    MultiByteToWideChar(CP_UTF8, 0, file_path.c_str(), -1, &wide_path[0], wlen);

    webview7->PrintToPdf(wide_path.c_str(), nullptr,
        Callback<ICoreWebView2PrintToPdfCompletedHandler>(
            [callback, webview7](HRESULT result, BOOL success) -> HRESULT {
                webview7->Release();
                callback(success ? S_OK : result);
                return S_OK;
            }).Get());
}

void ViewerWindow::ExportPlotly(const std::string& file_path,
                                  const std::string& format,
                                  std::function<void(bool)> callback) {
    if (!webview_ || !callback) return;

    // First check if Plotly is available
    const wchar_t* check_script = L"typeof window.Plotly !== 'undefined'";
    webview_->ExecuteScript(check_script,
        Callback<ICoreWebView2ExecuteScriptCompletedHandler>(
            [this, file_path, format, callback](HRESULT hr, LPCWSTR result) -> HRESULT {
                if (FAILED(hr) || !result) {
                    callback(false);
                    return S_OK;
                }

                int len = WideCharToMultiByte(CP_UTF8, 0, result, -1, nullptr, 0, nullptr, nullptr);
                std::string utf8(len - 1, 0);
                WideCharToMultiByte(CP_UTF8, 0, result, -1, &utf8[0], len, nullptr, nullptr);

                if (utf8 != "true") {
                    callback(false);
                    return S_OK;
                }

                // Plotly is available — call downloadImage
                // Escape backslashes in file path for JS
                std::string escaped_path = file_path;
                for (size_t i = 0; i < escaped_path.size(); i++) {
                    if (escaped_path[i] == '\\') {
                        escaped_path.insert(i, "\\");
                        i++;
                    }
                }

                std::string js = "Plotly.downloadImage(document.querySelector('.plotly-graph-div'), "
                    "{format:'" + format + "', filename:'" + escaped_path + "'})";

                int wlen2 = MultiByteToWideChar(CP_UTF8, 0, js.c_str(), -1, nullptr, 0);
                std::wstring wide_js(wlen2, 0);
                MultiByteToWideChar(CP_UTF8, 0, js.c_str(), -1, &wide_js[0], wlen2);

                webview_->ExecuteScript(wide_js.c_str(),
                    Callback<ICoreWebView2ExecuteScriptCompletedHandler>(
                        [callback](HRESULT hr2, LPCWSTR) -> HRESULT {
                            callback(SUCCEEDED(hr2));
                            return S_OK;
                        }).Get());

                return S_OK;
            }).Get());
}

// ─── Security ───────────────────────────────────────────────────────────

void ViewerWindow::ApplySecurityPolicy(bool dev_tools_enabled,
                                        const std::string& user_data_folder,
                                        bool advanced_mode,
                                        uint16_t pluto_port) {
    if (!webview_) return;

    ICoreWebView2Settings* settings = nullptr;
    webview_->get_Settings(&settings);
    if (settings) {
        settings->put_AreDevToolsEnabled(dev_tools_enabled ? TRUE : FALSE);
        settings->put_AreDefaultContextMenusEnabled(FALSE);
        settings->put_IsStatusBarEnabled(FALSE);
        settings->put_IsScriptEnabled(TRUE);  // Required for Plotly/D3.js interactivity
        settings->put_IsBuiltInErrorPageEnabled(FALSE);
        settings->Release();
    }

    // Navigation filter
    SetupNavigationFilter(user_data_folder, advanced_mode, pluto_port);
}

void ViewerWindow::SetupNavigationFilter(const std::string& user_data_folder,
                                          bool advanced_mode,
                                          uint16_t pluto_port) {
    if (!webview_) return;

    webview_->add_NavigationStarting(
        Callback<ICoreWebView2NavigationStartingEventHandler>(
            [user_data_folder, advanced_mode, pluto_port]
            (ICoreWebView2* sender, ICoreWebView2NavigationStartingEventArgs* args) -> HRESULT {
                LPWSTR uri = nullptr;
                args->get_Uri(&uri);
                if (!uri) return S_OK;

                std::wstring uri_str(uri);
                CoTaskMemFree(uri);

                // Always allow about:blank
                if (uri_str == L"about:blank") return S_OK;

                // Allow data: and blob: URIs (for Plotly image export, D3.js SVG)
                if (uri_str.find(L"data:") == 0 || uri_str.find(L"blob:") == 0) return S_OK;

                // Allow file:// URIs (local HTML content)
                if (uri_str.find(L"file:///") == 0) {
                    return S_OK;
                }

                // Allow trusted CDN domains (for Impress.js, Chart.js, SheetJS, Google Fonts)
                static const std::wstring trusted_cdn_prefixes[] = {
                    L"https://cdn.jsdelivr.net/",       // Impress.js, Chart.js
                    L"https://cdnjs.cloudflare.com/",   // SheetJS (xlsx)
                    L"https://fonts.googleapis.com/",   // Google Fonts CSS
                    L"https://fonts.gstatic.com/",      // Google Fonts files
                    L"https://unpkg.com/",              // Common JS CDN
                };
                for (const auto& prefix : trusted_cdn_prefixes) {
                    if (uri_str.find(prefix) == 0) {
                        return S_OK;
                    }
                }

                // Allow localhost:port when Advanced Mode is active
                if (advanced_mode) {
                    std::wstring localhost_prefix = L"http://localhost:" + std::to_wstring(pluto_port);
                    std::wstring localhost_prefix2 = L"http://127.0.0.1:" + std::to_wstring(pluto_port);
                    if (uri_str.find(localhost_prefix) == 0 || uri_str.find(localhost_prefix2) == 0) {
                        return S_OK;
                    }
                }

                // Block everything else
                args->put_Cancel(TRUE);
                RJ2XCL_LOG_WARN("ViewerWindow: navigation blocked: %ls", uri_str.c_str());
                return S_OK;
            }).Get(), nullptr);
}

// ─── Callbacks ──────────────────────────────────────────────────────────

void ViewerWindow::SetWebMessageCallback(WebMessageCallback callback) {
    web_message_callback_ = callback;
}

void ViewerWindow::SetCloseCallback(CloseCallback callback) {
    close_callback_ = callback;
}

// ─── Win32 Window Proc ──────────────────────────────────────────────────

LRESULT CALLBACK ViewerWindow::WindowProc(HWND hwnd, UINT msg,
                                           WPARAM wParam, LPARAM lParam) {
    ViewerWindow* self = nullptr;

    if (msg == WM_CREATE) {
        auto* cs = reinterpret_cast<CREATESTRUCT*>(lParam);
        self = static_cast<ViewerWindow*>(cs->lpCreateParams);
        SetWindowLongPtr(hwnd, GWLP_USERDATA, reinterpret_cast<LONG_PTR>(self));
    } else {
        self = reinterpret_cast<ViewerWindow*>(GetWindowLongPtr(hwnd, GWLP_USERDATA));
    }

    if (self) {
        return self->HandleMessage(msg, wParam, lParam);
    }

    return DefWindowProc(hwnd, msg, wParam, lParam);
}

LRESULT ViewerWindow::HandleMessage(UINT msg, WPARAM wParam, LPARAM lParam) {
    switch (msg) {
    case WM_SIZE:
        OnSize();
        return 0;

    case WM_CLOSE:
        OnClose();
        return 0;

    case WM_DESTROY:
        return 0;
    }

    return DefWindowProc(hwnd_, msg, wParam, lParam);
}

void ViewerWindow::OnSize() {
    if (controller_) {
        RECT bounds;
        GetClientRect(hwnd_, &bounds);
        controller_->put_Bounds(bounds);
    }
}

void ViewerWindow::OnClose() {
    if (close_callback_) {
        close_callback_(viewer_id_);
    }
    // Just hide — don't destroy. Set hwnd_ to null so IsViewerAlive detects it.
    // The actual cleanup happens when ViewerManager::CloseViewer deletes this object.
    ShowWindow(hwnd_, SW_HIDE);
    hwnd_ = nullptr;  // Signal that user closed this viewer
}

} // namespace rj2xcl
