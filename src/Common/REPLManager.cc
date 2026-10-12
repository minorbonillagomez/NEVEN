/**
 * Copyright (c) 2026 RJ2XCL Project — GPL v3
 *
 * @file REPLManager.cc
 * @brief Implementation of the WebView2 REPL console manager.
 */

#include "REPLManager.h"
#include "ViewerManager.h"
#include "DiagnosticRouter.h"
#include "ConfigService.h"
#include "LogService.h"

namespace rj2xcl {

// Static empty history for returning const reference when no history exists
const std::deque<std::string> REPLManager::empty_history_;

REPLManager::REPLManager()
    : last_active_language_("R")
{}

REPLManager::~REPLManager() {
    Shutdown();
}

REPLManager& REPLManager::Instance() {
    static REPLManager instance;
    return instance;
}

// ─── Console Lifecycle ──────────────────────────────────────────────────

std::string REPLManager::ShowConsole() {
    std::lock_guard<std::mutex> lock(mutex_);

    // Check if WebView2 is available
    if (!ViewerManager::Instance().IsAvailable()) {
        RJ2XCL_LOG_ERR("REPLManager: WebView2 not available");
        return "WebView2 not available — install Edge WebView2 Runtime";
    }

    // If console is already open and alive, bring to front
    if (!console_viewer_id_.empty() &&
        ViewerManager::Instance().IsViewerAlive(console_viewer_id_)) {
        RJ2XCL_LOG_INFO("REPLManager: bringing existing console to front: %s",
                        console_viewer_id_.c_str());
        // Send a focus message to the viewer
        ViewerManager::Instance().SendToViewer(console_viewer_id_,
            "{\"action\":\"focus\"}");
        return console_viewer_id_;
    }

    // Build path to repl.html
    std::string home = ConfigService::Instance().GetHomePath();
    std::string html_path = home + "console\\repl.html";

    // Create a new viewer from the HTML file
    std::string viewer_id = ViewerManager::Instance().CreateViewerFromFile(
        html_path, "REPL", "NEVEN Console");

    if (viewer_id.empty() || viewer_id.find("error") != std::string::npos) {
        RJ2XCL_LOG_ERR("REPLManager: failed to create console viewer: %s",
                       viewer_id.c_str());
        return viewer_id;
    }

    console_viewer_id_ = viewer_id;
    RJ2XCL_LOG_INFO("REPLManager: console opened with viewer_id=%s",
                    console_viewer_id_.c_str());

    // NOTE: Do NOT flush diagnostic buffer here — WebView2 is not ready yet.
    // Buffered diagnostics will be delivered when the console JS sends its
    // first "set-active-language" message (indicating it's fully loaded).

    return console_viewer_id_;
}

void REPLManager::HideConsole() {
    std::lock_guard<std::mutex> lock(mutex_);

    if (console_viewer_id_.empty()) return;

    if (ViewerManager::Instance().IsViewerAlive(console_viewer_id_)) {
        ViewerManager::Instance().CloseViewer(console_viewer_id_);
        RJ2XCL_LOG_INFO("REPLManager: console hidden");
    }
    // Keep console_viewer_id_ so we can detect it's been closed by user
    console_viewer_id_.clear();
}

void REPLManager::Shutdown() {
    std::lock_guard<std::mutex> lock(mutex_);

    if (!console_viewer_id_.empty()) {
        ViewerManager::Instance().CloseViewer(console_viewer_id_);
        console_viewer_id_.clear();
    }

    RJ2XCL_LOG_INFO("REPLManager: shutdown complete");
}

bool REPLManager::IsConsoleOpen() const {
    std::lock_guard<std::mutex> lock(mutex_);
    if (console_viewer_id_.empty()) return false;
    return ViewerManager::Instance().IsViewerAlive(console_viewer_id_);
}

std::string REPLManager::GetConsoleViewerId() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return console_viewer_id_;
}

// ─── Command History ────────────────────────────────────────────────────

void REPLManager::AddToHistory(const std::string& language, const std::string& command) {
    std::lock_guard<std::mutex> lock(mutex_);
    history_[language].Add(command);
}

const std::deque<std::string>& REPLManager::GetHistory(const std::string& language) const {
    std::lock_guard<std::mutex> lock(mutex_);
    auto it = history_.find(language);
    if (it == history_.end()) return empty_history_;
    return it->second.commands;
}

// ─── Active Language Tab ────────────────────────────────────────────────

std::string REPLManager::GetLastActiveLanguage() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return last_active_language_;
}

void REPLManager::SetLastActiveLanguage(const std::string& language) {
    std::lock_guard<std::mutex> lock(mutex_);
    last_active_language_ = language;
}

} // namespace rj2xcl
