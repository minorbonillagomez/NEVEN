/**
 * Copyright (c) 2026 RJ2XCL Project — GPL v3
 *
 * @file PlutoManager.cc
 * @brief Implementation of the Pluto.jl server manager.
 */

#include "PlutoManager.h"
#include "ViewerManager.h"
#include "LogService.h"
#include "ConfigService.h"
#include "DiscoveryService.h"

#include <sstream>
#include <winhttp.h>

#pragma comment(lib, "winhttp.lib")

namespace rj2xcl {

// ─── Singleton ──────────────────────────────────────────────────────────

PlutoManager& PlutoManager::Instance() {
    static PlutoManager instance;
    return instance;
}

PlutoManager::PlutoManager()
    : state_(State::STOPPED)
    , pluto_process_handle_(nullptr)
    , pluto_process_id_(0)
    , port_(1234)
    , started_by_this_session_(false)
{
}

PlutoManager::~PlutoManager() {
    Shutdown();
}

// ─── Lifecycle ──────────────────────────────────────────────────────────

void PlutoManager::Initialize() {
    // Read port from config
    auto& config = ConfigService::Instance();
    auto cfg = config.GetConfig();

    if (!cfg["Pluto"]["port"].is_null()) {
        int val = cfg["Pluto"]["port"].int_value();
        if (val < 1024) { val = 1024; RJ2XCL_LOG_WARN("Pluto.port clamped to 1024 (was %d)", cfg["Pluto"]["port"].int_value()); }
        if (val > 65535) { val = 65535; RJ2XCL_LOG_WARN("Pluto.port clamped to 65535"); }
        port_ = static_cast<uint16_t>(val);
    }

    // Fixed secret for Pluto — allows us to construct URLs deterministically
    pluto_secret_ = "rj2xcl";

    // Resolve Julia path via DiscoveryService
    auto julia_install = DiscoveryService::Instance().GetBestVersion("Julia", "", "");
    if (!julia_install.home_path.empty()) {
        julia_path_ = julia_install.home_path + "\\bin\\julia.exe";
        RJ2XCL_LOG_INFO("PlutoManager: Julia found at %s", julia_path_.c_str());
    } else {
        RJ2XCL_LOG_WARN("PlutoManager: Julia not found — Pluto Advanced Mode will not be available");
    }

    RJ2XCL_LOG_INFO("PlutoManager initialized (port %d, secret=%s)", port_, pluto_secret_.c_str());
}

void PlutoManager::Shutdown() {
    std::lock_guard<std::mutex> lock(state_mutex_);

    if (state_ != State::STOPPED && started_by_this_session_ && pluto_process_handle_) {
        RJ2XCL_LOG_INFO("Shutting down Pluto server (PID %d)", pluto_process_id_);

        // Try graceful termination first
        TerminateProcess(pluto_process_handle_, 0);
        DWORD result = WaitForSingleObject(pluto_process_handle_, 5000);
        if (result == WAIT_TIMEOUT) {
            RJ2XCL_LOG_WARN("Pluto process did not terminate in 5 seconds");
        }

        CloseHandle(pluto_process_handle_);
        pluto_process_handle_ = nullptr;
        pluto_process_id_ = 0;
    }

    // Close the Pluto viewer window if it exists
    if (!pluto_viewer_id_.empty()) {
        ViewerManager::Instance().CloseViewer(pluto_viewer_id_);
        pluto_viewer_id_.clear();
    }

    state_ = State::STOPPED;
    started_by_this_session_ = false;
    ViewerManager::Instance().SetAdvancedMode(false);
}

// ─── Server Control ─────────────────────────────────────────────────────

std::string PlutoManager::StartPluto() {
    std::lock_guard<std::mutex> lock(state_mutex_);

    if (state_ == State::RUNNING) {
        return "Pluto already running on port " + std::to_string(port_);
    }

    if (julia_path_.empty()) {
        return "Pluto server failed to start — check Julia installation";
    }

    // Kill any zombie julia processes occupying the Pluto port from a previous session.
    // Uses netstat to find only the specific process on our port (avoids killing ControlJulia).
    if (ProbePort(port_)) {
        RJ2XCL_LOG_WARN("Port %d occupied — attempting to free it", port_);

        // Find PID of process using the port via netstat
        char netstat_cmd[256];
        snprintf(netstat_cmd, sizeof(netstat_cmd),
                 "cmd /c \"for /f \"tokens=5\" %%a in ('netstat -ano ^| findstr :%d ^| findstr LISTENING') do taskkill /F /PID %%a\"",
                 port_);

        STARTUPINFOA kill_si = {};
        kill_si.cb = sizeof(kill_si);
        PROCESS_INFORMATION kill_pi = {};
        CreateProcessA(nullptr, netstat_cmd, nullptr, nullptr, FALSE,
                       CREATE_NO_WINDOW, nullptr, nullptr, &kill_si, &kill_pi);
        if (kill_pi.hProcess) {
            WaitForSingleObject(kill_pi.hProcess, 5000);
            CloseHandle(kill_pi.hProcess);
            CloseHandle(kill_pi.hThread);
        }
        Sleep(1000);  // Wait for port to be released
    }

    // Verify port is now free
    if (ProbePort(port_)) {
        RJ2XCL_LOG_WARN("Port %d still occupied after cleanup — using existing instance", port_);
        state_ = State::RUNNING;
        started_by_this_session_ = false;
        ViewerManager::Instance().SetAdvancedMode(true, port_);
        std::string url = "http://localhost:" + std::to_string(port_) + "/";
        pluto_viewer_id_ = ViewerManager::Instance().CreateViewerFromUrl(url, "Pluto.jl Notebooks");
        return "Pluto started on port " + std::to_string(port_);
    }

    // Build and launch Pluto command
    state_ = State::STARTING;
    std::string command = BuildPlutoCommand();

    STARTUPINFOA si;
    PROCESS_INFORMATION pi;
    ZeroMemory(&si, sizeof(si));
    si.cb = sizeof(si);
    ZeroMemory(&pi, sizeof(pi));

    // Launch as background process (no window)
    char cmd_buf[2048];
    strncpy_s(cmd_buf, command.c_str(), sizeof(cmd_buf) - 1);

    if (!CreateProcessA(nullptr, cmd_buf, nullptr, nullptr, FALSE,
                         CREATE_NO_WINDOW, nullptr, nullptr, &si, &pi)) {
        DWORD err = GetLastError();
        state_ = State::STOPPED;
        RJ2XCL_LOG_ERR("Failed to launch Pluto process: error %d", err);
        return "Pluto server failed to start — check Julia installation";
    }

    pluto_process_handle_ = pi.hProcess;
    pluto_process_id_ = pi.dwProcessId;
    CloseHandle(pi.hThread);

    RJ2XCL_LOG_INFO("Pluto process launched (PID %d), waiting for readiness...", pluto_process_id_);

    // Wait for Pluto to become ready
    if (!WaitForReady(30000)) {
        // Timeout — kill the process
        TerminateProcess(pluto_process_handle_, 1);
        CloseHandle(pluto_process_handle_);
        pluto_process_handle_ = nullptr;
        pluto_process_id_ = 0;
        state_ = State::STOPPED;
        RJ2XCL_LOG_ERR("Pluto server failed to start within 30 seconds");
        return "Pluto server failed to start — check Julia installation";
    }

    state_ = State::RUNNING;
    started_by_this_session_ = true;

    // Enable Advanced Mode and open viewer
    ViewerManager::Instance().SetAdvancedMode(true, port_);
    std::string url = "http://localhost:" + std::to_string(port_) + "/";
    pluto_viewer_id_ = ViewerManager::Instance().CreateViewerFromUrl(url, "Pluto.jl Notebooks");

    RJ2XCL_LOG_INFO("Pluto server started on port %d", port_);
    return "Pluto started on port " + std::to_string(port_);
}

std::string PlutoManager::StopPluto() {
    std::lock_guard<std::mutex> lock(state_mutex_);

    if (state_ == State::STOPPED) {
        return "Pluto already stopped";
    }

    if (started_by_this_session_ && pluto_process_handle_) {
        TerminateProcess(pluto_process_handle_, 0);
        WaitForSingleObject(pluto_process_handle_, 5000);
        CloseHandle(pluto_process_handle_);
        pluto_process_handle_ = nullptr;
        pluto_process_id_ = 0;
    }

    if (!pluto_viewer_id_.empty()) {
        ViewerManager::Instance().CloseViewer(pluto_viewer_id_);
        pluto_viewer_id_.clear();
    }

    ViewerManager::Instance().SetAdvancedMode(false);
    state_ = State::STOPPED;
    started_by_this_session_ = false;

    RJ2XCL_LOG_INFO("Pluto server stopped");
    return "Pluto stopped";
}

std::string PlutoManager::GetStatus() const {
    std::lock_guard<std::mutex> lock(state_mutex_);
    switch (state_) {
        case State::RUNNING:  return "running";
        case State::STARTING: return "starting";
        case State::STOPPED:
        default:              return "stopped";
    }
}

// ─── Notebook Operations ────────────────────────────────────────────────

std::string PlutoManager::OpenNotebook(const std::string& notebook_path) {
    if (state_ != State::RUNNING) {
        // Auto-start Pluto
        std::string result = StartPluto();
        if (state_ != State::RUNNING) {
            return result;  // Error message
        }
    }

    // Pluto 1.0+ URL: http://localhost:port/open?path=<path>
    // Convert backslashes to forward slashes (Pluto rejects Windows backslashes in URLs)
    std::string url_path = notebook_path;
    for (auto& c : url_path) { if (c == '\\') c = '/'; }
    std::string url = "http://localhost:" + std::to_string(port_) +
                      "/open?path=" + url_path;

    RJ2XCL_LOG_INFO("Opening notebook: %s → %s", notebook_path.c_str(), url.c_str());

    // Create a new viewer for the notebook URL
    pluto_viewer_id_ = ViewerManager::Instance().CreateViewerFromUrl(url, "Pluto — " + notebook_path);

    return pluto_viewer_id_;
}

// ─── Accessors ──────────────────────────────────────────────────────────

uint16_t PlutoManager::GetConfiguredPort() const {
    return port_;
}

bool PlutoManager::IsRunning() const {
    std::lock_guard<std::mutex> lock(state_mutex_);
    return state_ == State::RUNNING;
}

bool PlutoManager::WasStartedByThisSession() const {
    return started_by_this_session_;
}

// ─── Internal ───────────────────────────────────────────────────────────

bool PlutoManager::ProbePort(uint16_t port) const {
    // Simple HTTP probe to check if something is listening on the port
    HINTERNET hSession = WinHttpOpen(L"RJ2XCL/1.0", WINHTTP_ACCESS_TYPE_NO_PROXY,
                                      WINHTTP_NO_PROXY_NAME, WINHTTP_NO_PROXY_BYPASS, 0);
    if (!hSession) return false;

    std::wstring host = L"localhost";
    HINTERNET hConnect = WinHttpConnect(hSession, host.c_str(), port, 0);
    if (!hConnect) {
        WinHttpCloseHandle(hSession);
        return false;
    }

    HINTERNET hRequest = WinHttpOpenRequest(hConnect, L"GET", L"/",
                                             nullptr, WINHTTP_NO_REFERER,
                                             WINHTTP_DEFAULT_ACCEPT_TYPES, 0);
    if (!hRequest) {
        WinHttpCloseHandle(hConnect);
        WinHttpCloseHandle(hSession);
        return false;
    }

    // Set short timeout (2 seconds)
    DWORD timeout = 2000;
    WinHttpSetOption(hRequest, WINHTTP_OPTION_CONNECT_TIMEOUT, &timeout, sizeof(timeout));
    WinHttpSetOption(hRequest, WINHTTP_OPTION_RECEIVE_TIMEOUT, &timeout, sizeof(timeout));

    BOOL result = WinHttpSendRequest(hRequest, WINHTTP_NO_ADDITIONAL_HEADERS, 0,
                                      WINHTTP_NO_REQUEST_DATA, 0, 0, 0);
    bool is_running = false;
    if (result) {
        is_running = WinHttpReceiveResponse(hRequest, nullptr) ? true : false;
    }

    WinHttpCloseHandle(hRequest);
    WinHttpCloseHandle(hConnect);
    WinHttpCloseHandle(hSession);

    return is_running;
}

bool PlutoManager::WaitForReady(uint32_t timeout_ms) {
    DWORD start = GetTickCount();
    while ((GetTickCount() - start) < timeout_ms) {
        // Check if process is still alive
        DWORD exit_code = 0;
        if (GetExitCodeProcess(pluto_process_handle_, &exit_code) && exit_code != STILL_ACTIVE) {
            RJ2XCL_LOG_ERR("Pluto process exited prematurely with code %d", exit_code);
            return false;
        }

        if (ProbePort(port_)) {
            RJ2XCL_LOG_INFO("Pluto server ready after %d ms", GetTickCount() - start);
            return true;
        }

        Sleep(500);  // Poll every 500ms
    }
    return false;
}

std::string PlutoManager::BuildPlutoCommand() const {
    std::stringstream ss;
    ss << "\"" << julia_path_ << "\" "
       << "--project=@pluto "
       << "-e \"import Pluto; Pluto.run(host=\\\"127.0.0.1\\\", "
       << "port=" << port_ << ", "
       << "launch_browser=false, "
       << "auto_reload_from_file=true, "
       << "require_secret_for_access=false)\"";
    return ss.str();
}

} // namespace rj2xcl
