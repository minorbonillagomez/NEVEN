/**
 * Copyright (c) 2026 RJ2XCL Project — GPL v3
 *
 * @file ViewerManager.h
 * @brief Singleton managing the WebView2 viewer subsystem lifecycle.
 *
 * Handles WebView2 runtime detection, environment creation, viewer window
 * registry, FIFO eviction, and memory pressure monitoring. All WebView2
 * COM operations run on a dedicated STA thread.
 */

#pragma once

#include <string>
#include <vector>
#include <mutex>
#include <functional>
#include <cstdint>
#include <windows.h>

// Forward declarations — avoid pulling in WebView2.h in the header
struct ICoreWebView2Environment;

namespace rj2xcl {

class ViewerWindow;  // Forward declaration

/**
 * @brief Singleton that manages the WebView2 viewer subsystem.
 *
 * Lifecycle:
 *   1. Initialize() — detect runtime, create STA thread, create environment
 *   2. CreateViewer() / CloseViewer() — manage viewer windows
 *   3. Shutdown() — close all viewers, terminate STA thread
 */
class ViewerManager {
public:
    static ViewerManager& Instance();

    // ─── Lifecycle ───────────────────────────────────────────────────────

    /** @brief Initialize WebView2 subsystem. Called from RJ2XCL_Engine::Init(). */
    void Initialize();

    /** @brief Shutdown all viewers and release resources. Called from xlAutoClose. */
    void Shutdown();

    // ─── Runtime Detection ───────────────────────────────────────────────

    /**
     * @brief Returns true when WebView2 runtime is detected and environment created.
     * @return Availability status.
     */
    bool IsAvailable() const;

    // ─── Viewer Operations ───────────────────────────────────────────────

    /**
     * @brief Create a viewer window with inline HTML content.
     * @param html_content Complete HTML string.
     * @param language Source language ("R", "Julia", "Python").
     * @param title Window title.
     * @return Viewer identifier string ("viewer-N") or error string.
     */
    std::string CreateViewer(const std::string& html_content,
                             const std::string& language,
                             const std::string& title);

    /**
     * @brief Create a viewer window from an HTML file.
     * @param file_path Path to the HTML file.
     * @param language Source language.
     * @param title Window title.
     * @return Viewer identifier string or error string.
     */
    std::string CreateViewerFromFile(const std::string& file_path,
                                     const std::string& language,
                                     const std::string& title);

    /**
     * @brief Create a viewer window navigated to a URL (for Pluto Advanced Mode).
     * @param url URL to navigate to (e.g., http://localhost:1234).
     * @param title Window title.
     * @return Viewer identifier string or error string.
     */
    std::string CreateViewerFromUrl(const std::string& url,
                                    const std::string& title);

    /**
     * @brief Close a specific viewer window.
     * @param viewer_id The viewer identifier.
     * @return true if the viewer was found and closed.
     */
    bool CloseViewer(const std::string& viewer_id);

    /** @brief Close all active viewer windows. */
    void CloseAllViewers();

    /**
     * @brief List all active viewer identifiers.
     * @return Vector of viewer ID strings.
     */
    std::vector<std::string> ListViewers() const;

    // ─── Communication ───────────────────────────────────────────────────

    /**
     * @brief Send a JSON message to a specific viewer's JavaScript context.
     * @param viewer_id Target viewer.
     * @param json_message JSON string to send.
     * @return true if the message was sent successfully.
     */
    bool SendToViewer(const std::string& viewer_id,
                      const std::string& json_message);

    /**
     * @brief Capture the current HTML content of a viewer (for PresentationBuilder).
     * @param viewer_id Target viewer.
     * @return HTML content string, or empty string if not found.
     */
    std::string CaptureViewerContent(const std::string& viewer_id);

    /**
     * @brief Asynchronously captures the rendered DOM HTML of a viewer.
     * @param viewer_id The viewer to capture from.
     * @param callback Called with the HTML string (or empty on failure).
     */
    void CaptureViewerPageSource(const std::string& viewer_id,
                                  std::function<void(const std::string&)> callback);

    // ─── Viewer Reuse ────────────────────────────────────────────────────

    /**
     * @brief Navigate an existing viewer to new HTML content (reuse window).
     * @param viewer_id Target viewer.
     * @param html_content New HTML string to display.
     * @return true if the viewer was found and navigation initiated.
     */
    bool NavigateViewerToString(const std::string& viewer_id,
                                const std::string& html_content);

    /**
     * @brief Navigate an existing viewer to a file URL (reuse window).
     * @param viewer_id Target viewer.
     * @param file_path Path to the HTML file.
     * @return true if the viewer was found and navigation initiated.
     */
    bool NavigateViewerToFile(const std::string& viewer_id,
                              const std::string& file_path);

    /**
     * @brief Check if a viewer is still alive (window exists and is valid).
     * @param viewer_id Target viewer.
     * @return true if the viewer exists and has a valid window.
     */
    bool IsViewerAlive(const std::string& viewer_id) const;

    // ─── Advanced Mode (Pluto) ───────────────────────────────────────────

    /**
     * @brief Enable/disable Advanced Mode navigation policy (allows localhost).
     * @param active Whether Advanced Mode is active.
     * @param pluto_port The Pluto server port.
     */
    void SetAdvancedMode(bool active, uint16_t pluto_port = 1234);
    bool IsAdvancedModeActive() const;
    uint16_t GetAdvancedModePort() const;

private:
    ViewerManager();
    ~ViewerManager();
    ViewerManager(const ViewerManager&) = delete;
    ViewerManager& operator=(const ViewerManager&) = delete;

    // ─── STA Thread ──────────────────────────────────────────────────────

    static unsigned __stdcall STAThreadProc(void* param);
    void RunSTAThread();
    void InitializeEnvironment();

    // ─── Memory Management ───────────────────────────────────────────────

    void ProcessMemoryPressure();
    void EvictOldestViewer();

    // ─── Internal State ──────────────────────────────────────────────────

    bool available_;
    bool advanced_mode_active_;
    uint16_t advanced_mode_port_;

    DWORD sta_thread_id_;
    HANDLE sta_thread_handle_;
    HANDLE environment_ready_event_;

    ICoreWebView2Environment* environment_;

    struct ViewerEntry {
        std::string id;
        std::string language;
        std::string title;
        ViewerWindow* window;
        FILETIME created_at;
        size_t content_size_bytes;
        size_t content_hash = 0;
    };

    std::vector<ViewerEntry> viewers_;
    mutable std::mutex viewers_mutex_;
    uint32_t next_viewer_id_;
    uint32_t max_viewers_;
    uint32_t max_memory_mb_;
};

} // namespace rj2xcl
