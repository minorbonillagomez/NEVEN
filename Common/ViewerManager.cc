/**
 * Copyright (c) 2026 RJ2XCL Project — GPL v3
 *
 * @file ViewerManager.cc
 * @brief Implementation of the WebView2 ViewerManager singleton.
 */

#include "ViewerManager.h"
#include "ViewerWindow.h"
#include "PostMessageBridge.h"
#include "REPLBridge.h"
#include "REPLManager.h"
#include "DiagnosticRouter.h"
#include "LogService.h"
#include "ConfigService.h"

#include <WebView2.h>
#include <wrl.h>
#include <process.h>
#include <sstream>

using Microsoft::WRL::Callback;

namespace rj2xcl {

// ─── Custom Window Messages for STA Thread ──────────────────────────────

static constexpr UINT WM_APP_CREATE_VIEWER    = WM_APP + 100;
static constexpr UINT WM_APP_NAVIGATE_STRING  = WM_APP + 101;
static constexpr UINT WM_APP_NAVIGATE_FILE    = WM_APP + 102;
static constexpr UINT WM_APP_SEND_MESSAGE     = WM_APP + 103;
static constexpr UINT WM_APP_CLOSE_VIEWER     = WM_APP + 104;
static constexpr UINT WM_APP_SAVE_CONTENT     = WM_APP + 105;

// Timer ID for diagnostic queue draining (50ms interval)
static constexpr UINT_PTR DIAGNOSTIC_TIMER_ID = 1001;

// Request struct for STA thread communication
struct CreateViewerRequest {
    std::string viewer_id;
    std::string html_content;
    std::string url;
    std::string title;
    int width;
    int height;
};

// Request struct for sending messages to a viewer
struct SendMessageRequest {
    std::string viewer_id;
    std::string json_message;
};

// Request struct for save operations
struct SaveContentRequest {
    std::string viewer_id;
    std::string file_path;
    std::string format;  // "html", "png", "pdf"
};

// ─── Singleton ──────────────────────────────────────────────────────────

ViewerManager& ViewerManager::Instance() {
    static ViewerManager instance;
    return instance;
}

ViewerManager::ViewerManager()
    : available_(false)
    , advanced_mode_active_(false)
    , advanced_mode_port_(1234)
    , sta_thread_id_(0)
    , sta_thread_handle_(nullptr)
    , environment_ready_event_(nullptr)
    , environment_(nullptr)
    , next_viewer_id_(1)
    , max_viewers_(8)
    , max_memory_mb_(512)
{
}

ViewerManager::~ViewerManager() {
    Shutdown();
}

// ─── Lifecycle ──────────────────────────────────────────────────────────

void ViewerManager::Initialize() {
    // Check if WebView2 is enabled in config
    auto& config = ConfigService::Instance();
    auto cfg = config.GetConfig();
    
    bool enabled = true;
    if (!cfg["WebView2"]["enabled"].is_null()) {
        enabled = cfg["WebView2"]["enabled"].bool_value();
    }
    if (!enabled) {
        RJ2XCL_LOG_INFO("WebView2 disabled via configuration");
        available_ = false;
        return;
    }

    // Read config values
    if (!cfg["WebView2"]["maxViewers"].is_null()) {
        int val = cfg["WebView2"]["maxViewers"].int_value();
        if (val < 1) { val = 1; RJ2XCL_LOG_WARN("WebView2.maxViewers clamped to 1 (was %d)", cfg["WebView2"]["maxViewers"].int_value()); }
        if (val > 16) { val = 16; RJ2XCL_LOG_WARN("WebView2.maxViewers clamped to 16 (was %d)", cfg["WebView2"]["maxViewers"].int_value()); }
        max_viewers_ = static_cast<uint32_t>(val);
    }
    if (!cfg["WebView2"]["maxMemoryMB"].is_null()) {
        int val = cfg["WebView2"]["maxMemoryMB"].int_value();
        if (val < 128) { val = 128; RJ2XCL_LOG_WARN("WebView2.maxMemoryMB clamped to 128"); }
        if (val > 2048) { val = 2048; RJ2XCL_LOG_WARN("WebView2.maxMemoryMB clamped to 2048"); }
        max_memory_mb_ = static_cast<uint32_t>(val);
    }

    // Detect WebView2 runtime
    LPWSTR version_info = nullptr;
    HRESULT hr = GetAvailableCoreWebView2BrowserVersionString(nullptr, &version_info);
    
    if (FAILED(hr) || version_info == nullptr) {
        RJ2XCL_LOG_WARN("WebView2 runtime not found — interactive viewer disabled");
        available_ = false;
        return;
    }

    RJ2XCL_LOG_INFO("WebView2 runtime detected: %ls", version_info);
    CoTaskMemFree(version_info);

    // Create event for environment readiness signaling
    environment_ready_event_ = CreateEvent(nullptr, TRUE, FALSE, nullptr);

    // Launch STA thread for WebView2 COM operations
    sta_thread_handle_ = (HANDLE)_beginthreadex(
        nullptr, 0, STAThreadProc, this, 0, (unsigned*)&sta_thread_id_);

    if (!sta_thread_handle_) {
        RJ2XCL_LOG_ERR("Failed to create STA thread for WebView2");
        available_ = false;
        return;
    }

    // Don't wait for environment — let it initialize asynchronously.
    // The STA thread will set available_ = true when ready.
    // This prevents blocking Excel startup.
    available_ = true;  // Optimistic — will be set to false if environment fails
    RJ2XCL_LOG_INFO("WebView2 viewer subsystem initializing asynchronously (max %d viewers, %d MB limit)",
                     max_viewers_, max_memory_mb_);
}

void ViewerManager::Shutdown() {
    CloseAllViewers();

    // Terminate STA thread
    if (sta_thread_id_) {
        PostThreadMessage(sta_thread_id_, WM_QUIT, 0, 0);
        if (sta_thread_handle_) {
            DWORD result = WaitForSingleObject(sta_thread_handle_, 5000);
            if (result == WAIT_TIMEOUT) {
                RJ2XCL_LOG_ERR("STA thread did not terminate in 5 seconds — forcing");
                TerminateThread(sta_thread_handle_, 1);
            }
            CloseHandle(sta_thread_handle_);
            sta_thread_handle_ = nullptr;
        }
        sta_thread_id_ = 0;
    }

    // Release environment
    if (environment_) {
        environment_->Release();
        environment_ = nullptr;
    }

    if (environment_ready_event_) {
        CloseHandle(environment_ready_event_);
        environment_ready_event_ = nullptr;
    }

    available_ = false;
    RJ2XCL_LOG_INFO("WebView2 viewer subsystem shut down");
}

// ─── Runtime Detection ──────────────────────────────────────────────────

bool ViewerManager::IsAvailable() const {
    return available_;
}

// ─── STA Thread ─────────────────────────────────────────────────────────

unsigned __stdcall ViewerManager::STAThreadProc(void* param) {
    auto* self = static_cast<ViewerManager*>(param);
    self->RunSTAThread();
    return 0;
}

void ViewerManager::RunSTAThread() {
    // Initialize COM as STA (required for WebView2)
    CoInitializeEx(nullptr, COINIT_APARTMENTTHREADED);

    // Create WebView2 environment
    InitializeEnvironment();

    // No diagnostic timer — delivery is triggered by PostThreadMessage
    // from DiagnosticRouter when messages arrive and console is open.
    UINT_PTR diagnostic_timer = 0;

    // Message pump — processes WM_APP_* messages from the Excel UI thread
    MSG msg;
    while (GetMessage(&msg, nullptr, 0, 0)) {
        if (msg.hwnd == nullptr) {
            // Thread message (not window message) — handle custom commands
            switch (msg.message) {
            case WM_TIMER:
                // Diagnostic queue drain timer
                if (msg.wParam == DIAGNOSTIC_TIMER_ID) {
                    DiagnosticRouter::Instance().DeliverPending();
                }
                break;
            case WM_APP_CREATE_VIEWER:
            {
                // wParam = pointer to CreateViewerRequest struct
                auto* req = reinterpret_cast<CreateViewerRequest*>(msg.wParam);
                if (req && environment_) {
                    HWND excel_hwnd = FindWindowA("XLMAIN", nullptr);
                    auto* window = new ViewerWindow(
                        excel_hwnd, environment_, req->viewer_id, req->title,
                        req->width, req->height);

                    // Apply security policy
                    auto& config = ConfigService::Instance();
                    window->ApplySecurityPolicy(
                        config.IsDevToolsEnabled(),
                        config.GetWebView2UserDataFolder(),
                        advanced_mode_active_,
                        advanced_mode_port_);

                    // Navigate to content
                    if (!req->url.empty()) {
                        window->NavigateToUrl(req->url);
                    } else if (!req->html_content.empty()) {
                        window->NavigateToString(req->html_content);
                    }

                    window->Show();

                    // Set WebMessage callback — routes to REPLBridge or PostMessageBridge
                    window->SetWebMessageCallback(
                        [](const std::string& viewer_id, const std::string& json_message) {
                            // Check if this viewer is the REPL console
                            std::string repl_id = REPLManager::Instance().GetConsoleViewerId();
                            if (!repl_id.empty() && viewer_id == repl_id) {
                                REPLBridge::OnWebMessageReceived(viewer_id, json_message);
                            } else {
                                PostMessageBridge::OnWebMessageReceived(viewer_id, json_message, nullptr);
                            }
                        });

                    // Set close callback to clean up REPL state if console is closed
                    window->SetCloseCallback(
                        [](const std::string& viewer_id) {
                            RJ2XCL_LOG_INFO("ViewerWindow closed: %s", viewer_id.c_str());
                        });

                    // Update the registry entry with the window pointer
                    {
                        std::lock_guard<std::mutex> lock(viewers_mutex_);
                        for (auto& entry : viewers_) {
                            if (entry.id == req->viewer_id) {
                                entry.window = window;
                                break;
                            }
                        }
                    }

                    RJ2XCL_LOG_INFO("ViewerWindow created on STA thread: %s", req->viewer_id.c_str());
                }
                delete req;
                break;
            }
            case WM_APP_CLOSE_VIEWER:
            {
                auto* id = reinterpret_cast<std::string*>(msg.wParam);
                if (id) {
                    std::lock_guard<std::mutex> lock(viewers_mutex_);
                    for (auto& entry : viewers_) {
                        if (entry.id == *id && entry.window) {
                            delete entry.window;
                            entry.window = nullptr;
                            break;
                        }
                    }
                }
                delete id;
                break;
            }
            case WM_APP_SEND_MESSAGE:
            {
                auto* req = reinterpret_cast<SendMessageRequest*>(msg.wParam);
                if (req) {
                    std::lock_guard<std::mutex> lock(viewers_mutex_);
                    for (auto& entry : viewers_) {
                        if (entry.id == req->viewer_id && entry.window) {
                            HRESULT hr = entry.window->PostWebMessage(req->json_message);
                            if (SUCCEEDED(hr)) {
                                RJ2XCL_LOG_INFO("STA: PostWebMessage OK for %s", req->viewer_id.c_str());
                            } else {
                                RJ2XCL_LOG_WARN("STA: PostWebMessage failed for %s (0x%08X)",
                                                 req->viewer_id.c_str(), hr);
                            }
                            break;
                        }
                    }
                }
                delete req;
                break;
            }
            case WM_APP_SAVE_CONTENT:
            {
                auto* req = reinterpret_cast<SaveContentRequest*>(msg.wParam);
                if (req) {
                    std::lock_guard<std::mutex> lock(viewers_mutex_);
                    for (auto& entry : viewers_) {
                        if (entry.id == req->viewer_id && entry.window) {
                            if (req->format == "png") {
                                entry.window->ExportPlotly(req->file_path, "png",
                                    [&entry, file_path = req->file_path](bool plotly_ok) {
                                        if (!plotly_ok) {
                                            entry.window->CaptureAsPng(file_path,
                                                [](HRESULT) {});
                                        }
                                    });
                            } else if (req->format == "pdf") {
                                entry.window->ExportPlotly(req->file_path, "pdf",
                                    [&entry, file_path = req->file_path](bool plotly_ok) {
                                        if (!plotly_ok) {
                                            entry.window->PrintToPdf(file_path,
                                                [](HRESULT) {});
                                        }
                                    });
                            }
                            break;
                        }
                    }
                }
                delete req;
                break;
            }
            default:
                break;
            }
        } else {
            TranslateMessage(&msg);
            DispatchMessage(&msg);
        }
    }

    // Kill diagnostic timer before shutdown
    if (diagnostic_timer) {
        KillTimer(NULL, diagnostic_timer);
    }

    CoUninitialize();
}

void ViewerManager::InitializeEnvironment() {
    // Resolve user data folder
    std::string user_data_folder;
    auto& config = ConfigService::Instance();
    auto cfg = config.GetConfig();
    
    if (!cfg["WebView2"]["userDataFolder"].is_null()) {
        user_data_folder = cfg["WebView2"]["userDataFolder"].string_value();
    }
    if (user_data_folder.empty()) {
        user_data_folder = config.GetHomePath() + "webview2-data";
    }

    // Convert to wide string for COM API
    int wlen = MultiByteToWideChar(CP_UTF8, 0, user_data_folder.c_str(), -1, nullptr, 0);
    std::wstring wide_folder(wlen, 0);
    MultiByteToWideChar(CP_UTF8, 0, user_data_folder.c_str(), -1, &wide_folder[0], wlen);

    HRESULT hr = CreateCoreWebView2EnvironmentWithOptions(
        nullptr,                    // browserExecutableFolder (use default Edge)
        wide_folder.c_str(),        // userDataFolder
        nullptr,                    // additionalBrowserArguments
        Callback<ICoreWebView2CreateCoreWebView2EnvironmentCompletedHandler>(
            [this](HRESULT result, ICoreWebView2Environment* env) -> HRESULT {
                if (SUCCEEDED(result) && env) {
                    environment_ = env;
                    environment_->AddRef();
                    RJ2XCL_LOG_INFO("WebView2 environment created successfully");
                } else {
                    RJ2XCL_LOG_ERR("WebView2 environment creation failed: HRESULT 0x%08X", result);
                }
                SetEvent(environment_ready_event_);
                return S_OK;
            }).Get());

    if (FAILED(hr)) {
        RJ2XCL_LOG_ERR("CreateCoreWebView2EnvironmentWithOptions failed: HRESULT 0x%08X", hr);
        SetEvent(environment_ready_event_);
    }
}

// ─── Viewer Operations ──────────────────────────────────────────────────

std::string ViewerManager::CreateViewer(const std::string& html_content,
                                         const std::string& language,
                                         const std::string& title) {
    if (!available_) {
        return "WebView2 not available — install Edge WebView2 Runtime";
    }

    if (html_content.empty()) {
        RJ2XCL_LOG_WARN("Empty HTML content — not creating viewer");
        return "Error: empty HTML content";
    }

    // FIFO eviction if at max
    {
        std::lock_guard<std::mutex> lock(viewers_mutex_);
        if (viewers_.size() >= max_viewers_) {
            EvictOldestViewer();
        }
    }

    // Generate unique ID
    std::stringstream ss;
    ss << "viewer-" << next_viewer_id_++;
    std::string viewer_id = ss.str();

    // Create entry
    ViewerEntry entry;
    entry.id = viewer_id;
    entry.language = language;
    entry.title = title;
    entry.window = nullptr;
    GetSystemTimeAsFileTime(&entry.created_at);
    entry.content_size_bytes = html_content.size();

    {
        std::lock_guard<std::mutex> lock(viewers_mutex_);
        viewers_.push_back(entry);
    }

    // Post request to STA thread to create the actual window
    auto* req = new CreateViewerRequest();
    req->viewer_id = viewer_id;
    req->html_content = html_content;
    req->title = "NEVEN - " + title;
    req->width = 800;
    req->height = 600;
    PostThreadMessage(sta_thread_id_, WM_APP_CREATE_VIEWER, reinterpret_cast<WPARAM>(req), 0);

    RJ2XCL_LOG_INFO("Viewer created: %s (%s — %s, %zu bytes)",
                     viewer_id.c_str(), language.c_str(), title.c_str(), html_content.size());

    return viewer_id;
}

std::string ViewerManager::CreateViewerFromFile(const std::string& file_path,
                                                 const std::string& language,
                                                 const std::string& title) {
    if (!available_) {
        return "WebView2 not available — install Edge WebView2 Runtime";
    }

    // Verify file exists
    DWORD attrs = GetFileAttributesA(file_path.c_str());
    if (attrs == INVALID_FILE_ATTRIBUTES) {
        RJ2XCL_LOG_WARN("HTML file not found: %s", file_path.c_str());
        return "Error: file not found — " + file_path;
    }

    // FIFO eviction
    {
        std::lock_guard<std::mutex> lock(viewers_mutex_);
        if (viewers_.size() >= max_viewers_) {
            EvictOldestViewer();
        }
    }

    // Generate unique ID
    std::stringstream ss;
    ss << "viewer-" << next_viewer_id_++;
    std::string viewer_id = ss.str();

    ViewerEntry entry;
    entry.id = viewer_id;
    entry.language = language;
    entry.title = title;
    entry.window = nullptr;
    GetSystemTimeAsFileTime(&entry.created_at);
    entry.content_size_bytes = 0;

    {
        std::lock_guard<std::mutex> lock(viewers_mutex_);
        viewers_.push_back(entry);
    }

    // Build file:// URL
    std::string file_url = "file:///" + file_path;
    for (auto& c : file_url) { if (c == '\\') c = '/'; }

    // Post request to STA thread
    auto* req = new CreateViewerRequest();
    req->viewer_id = viewer_id;
    req->url = file_url;
    req->title = "NEVEN - " + title;
    req->width = 1024;
    req->height = 768;
    PostThreadMessage(sta_thread_id_, WM_APP_CREATE_VIEWER, reinterpret_cast<WPARAM>(req), 0);

    RJ2XCL_LOG_INFO("File viewer created: %s (%s)", viewer_id.c_str(), file_path.c_str());
    return viewer_id;
}

std::string ViewerManager::CreateViewerFromUrl(const std::string& url,
                                                const std::string& title) {
    if (!available_) {
        return "WebView2 not available — install Edge WebView2 Runtime";
    }

    // Generate unique ID
    std::stringstream ss;
    ss << "viewer-" << next_viewer_id_++;
    std::string viewer_id = ss.str();

    ViewerEntry entry;
    entry.id = viewer_id;
    entry.language = "Pluto";
    entry.title = title;
    entry.window = nullptr;
    GetSystemTimeAsFileTime(&entry.created_at);
    entry.content_size_bytes = 0;

    {
        std::lock_guard<std::mutex> lock(viewers_mutex_);
        viewers_.push_back(entry);
    }

    // Post request to STA thread
    auto* req = new CreateViewerRequest();
    req->viewer_id = viewer_id;
    req->url = url;
    req->title = "NEVEN - Pluto.jl - " + title;
    req->width = 1024;
    req->height = 768;
    PostThreadMessage(sta_thread_id_, WM_APP_CREATE_VIEWER, reinterpret_cast<WPARAM>(req), 0);

    RJ2XCL_LOG_INFO("URL viewer created: %s (%s)", viewer_id.c_str(), url.c_str());
    return viewer_id;
}

bool ViewerManager::CloseViewer(const std::string& viewer_id) {
    std::lock_guard<std::mutex> lock(viewers_mutex_);
    for (auto it = viewers_.begin(); it != viewers_.end(); ++it) {
        if (it->id == viewer_id) {
            if (it->window) {
                delete it->window;
                it->window = nullptr;
            }
            RJ2XCL_LOG_INFO("Viewer closed: %s", viewer_id.c_str());
            viewers_.erase(it);
            return true;
        }
    }
    RJ2XCL_LOG_WARN("Viewer not found: %s", viewer_id.c_str());
    return false;
}

void ViewerManager::CloseAllViewers() {
    std::lock_guard<std::mutex> lock(viewers_mutex_);
    for (auto& entry : viewers_) {
        if (entry.window) {
            delete entry.window;
            entry.window = nullptr;
        }
    }
    viewers_.clear();
    RJ2XCL_LOG_INFO("All viewers closed");
}

std::vector<std::string> ViewerManager::ListViewers() const {
    std::lock_guard<std::mutex> lock(viewers_mutex_);
    std::vector<std::string> ids;
    ids.reserve(viewers_.size());
    for (const auto& entry : viewers_) {
        ids.push_back(entry.id);
    }
    return ids;
}

// ─── Communication ──────────────────────────────────────────────────────

bool ViewerManager::SendToViewer(const std::string& viewer_id,
                                  const std::string& json_message) {
    // Verify the viewer exists before posting to STA thread
    {
        std::lock_guard<std::mutex> lock(viewers_mutex_);
        bool found = false;
        for (const auto& entry : viewers_) {
            if (entry.id == viewer_id && entry.window) {
                found = true;
                break;
            }
        }
        if (!found) {
            RJ2XCL_LOG_WARN("SendToViewer: viewer '%s' not found in registry (%zu viewers active)",
                             viewer_id.c_str(), viewers_.size());
            return false;
        }
    }

    // Marshal the call to the STA thread where WebView2 COM lives
    auto* req = new SendMessageRequest();
    req->viewer_id = viewer_id;
    req->json_message = json_message;
    BOOL posted = PostThreadMessage(sta_thread_id_, WM_APP_SEND_MESSAGE,
                                     reinterpret_cast<WPARAM>(req), 0);
    if (!posted) {
        RJ2XCL_LOG_WARN("SendToViewer: PostThreadMessage failed for %s (error %d)",
                         viewer_id.c_str(), GetLastError());
        delete req;
        return false;
    }

    RJ2XCL_LOG_INFO("SendToViewer: queued message for %s (%zu bytes)",
                     viewer_id.c_str(), json_message.size());
    return true;
}

std::string ViewerManager::CaptureViewerContent(const std::string& viewer_id) {
    std::lock_guard<std::mutex> lock(viewers_mutex_);
    for (const auto& entry : viewers_) {
        if (entry.id == viewer_id && entry.window) {
            return entry.window->GetCurrentContent();
        }
    }
    return "";
}

void ViewerManager::CaptureViewerPageSource(const std::string& viewer_id,
                                             std::function<void(const std::string&)> callback) {
    std::lock_guard<std::mutex> lock(viewers_mutex_);
    for (auto& entry : viewers_) {
        if (entry.id == viewer_id && entry.window) {
            entry.window->GetPageSource(callback);
            return;
        }
    }
    if (callback) callback("");
}

// ─── Viewer Reuse ───────────────────────────────────────────────────────

bool ViewerManager::NavigateViewerToString(const std::string& viewer_id,
                                            const std::string& html_content) {
    std::lock_guard<std::mutex> lock(viewers_mutex_);
    for (auto& entry : viewers_) {
        if (entry.id == viewer_id && entry.window) {
            entry.window->NavigateToString(html_content);
            entry.content_size_bytes = html_content.size();
            RJ2XCL_LOG_INFO("Viewer reused: %s (navigated to new HTML, %zu bytes)",
                             viewer_id.c_str(), html_content.size());
            return true;
        }
    }
    return false;
}

bool ViewerManager::NavigateViewerToFile(const std::string& viewer_id,
                                          const std::string& file_path) {
    std::lock_guard<std::mutex> lock(viewers_mutex_);
    for (auto& entry : viewers_) {
        if (entry.id == viewer_id && entry.window) {
            // Navigate to file — WebView2 will reload since content changed on disk
            entry.window->NavigateToFile(file_path);
            entry.content_size_bytes = 0;
            RJ2XCL_LOG_INFO("Viewer reused: %s (navigated to file: %s)",
                             viewer_id.c_str(), file_path.c_str());
            return true;
        }
    }
    return false;
}

bool ViewerManager::IsViewerAlive(const std::string& viewer_id) const {
    std::lock_guard<std::mutex> lock(viewers_mutex_);
    for (const auto& entry : viewers_) {
        if (entry.id == viewer_id && entry.window) {
            HWND hwnd = entry.window->GetHwnd();
            return hwnd != nullptr && IsWindow(hwnd);
        }
    }
    return false;
}

// ─── Advanced Mode ──────────────────────────────────────────────────────

void ViewerManager::SetAdvancedMode(bool active, uint16_t pluto_port) {
    advanced_mode_active_ = active;
    advanced_mode_port_ = pluto_port;
    RJ2XCL_LOG_INFO("Advanced Mode %s (port %d)", active ? "enabled" : "disabled", pluto_port);
}

bool ViewerManager::IsAdvancedModeActive() const {
    return advanced_mode_active_;
}

uint16_t ViewerManager::GetAdvancedModePort() const {
    return advanced_mode_port_;
}

// ─── Memory Management ──────────────────────────────────────────────────

void ViewerManager::ProcessMemoryPressure() {
    size_t total_bytes = 0;
    for (const auto& entry : viewers_) {
        total_bytes += entry.content_size_bytes;
    }

    size_t limit_bytes = static_cast<size_t>(max_memory_mb_) * 1024 * 1024;
    if (total_bytes > limit_bytes) {
        RJ2XCL_LOG_WARN("WebView2 memory pressure: %zu MB > %u MB limit — evicting oldest viewer",
                         total_bytes / (1024 * 1024), max_memory_mb_);
        EvictOldestViewer();
    }
}

void ViewerManager::EvictOldestViewer() {
    // viewers_mutex_ must be held by caller
    if (viewers_.empty()) return;

    // Find oldest by created_at
    auto oldest = viewers_.begin();
    for (auto it = viewers_.begin(); it != viewers_.end(); ++it) {
        if (CompareFileTime(&it->created_at, &oldest->created_at) < 0) {
            oldest = it;
        }
    }

    RJ2XCL_LOG_INFO("Evicting oldest viewer: %s", oldest->id.c_str());
    if (oldest->window) {
        delete oldest->window;
        oldest->window = nullptr;
    }
    viewers_.erase(oldest);
}

} // namespace rj2xcl
