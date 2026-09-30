/**
 * Copyright (c) 2026 RJ2XCL Project — GPL v3
 *
 * @file ViewerWindow.h
 * @brief Win32 modeless window hosting a WebView2 controller.
 *
 * Each ViewerWindow is a floating panel owned by the Excel main window.
 * It hosts an ICoreWebView2Controller that renders HTML content.
 */

#pragma once

#include <string>
#include <windows.h>
#include <functional>

// Forward declarations
struct ICoreWebView2Environment;
struct ICoreWebView2Controller;
struct ICoreWebView2;

namespace rj2xcl {

/**
 * @brief A Win32 modeless window that hosts a WebView2 controller.
 *
 * Created on the STA thread. Owned by the Excel main window so it
 * minimizes/restores with Excel.
 */
class ViewerWindow {
public:
    /**
     * @brief Construct a viewer window.
     * @param parent_hwnd Excel main window handle (owner).
     * @param environment WebView2 environment for controller creation.
     * @param viewer_id Unique identifier (e.g., "viewer-1").
     * @param title Window title.
     * @param width Initial width in pixels.
     * @param height Initial height in pixels.
     */
    ViewerWindow(HWND parent_hwnd,
                 ICoreWebView2Environment* environment,
                 const std::string& viewer_id,
                 const std::string& title,
                 int width = 800,
                 int height = 600);

    ~ViewerWindow();

    // ─── Navigation ──────────────────────────────────────────────────────

    /** @brief Load inline HTML content (< 2 MB). */
    HRESULT NavigateToString(const std::string& html);

    /** @brief Load HTML from a file path. */
    HRESULT NavigateToFile(const std::string& file_path);

    /** @brief Navigate to a URL (for Pluto Advanced Mode). */
    HRESULT NavigateToUrl(const std::string& url);

    /** @brief Reload the current page (forces re-read of file from disk). */
    HRESULT Reload();

    // ─── Communication ───────────────────────────────────────────────────

    /** @brief Send a JSON message to the JavaScript context. */
    HRESULT PostWebMessage(const std::string& json);

    // ─── Window Management ───────────────────────────────────────────────

    void Show();
    void Hide();
    void Resize(int width, int height);
    void SetTitle(const std::string& title);
    HWND GetHwnd() const;
    std::string GetViewerId() const;

    // ─── Save Operations ────────────────────────────────────────────────

    /**
     * @brief Get page source via ExecuteScript("document.documentElement.outerHTML").
     * @param callback Called with the HTML string result.
     */
    void GetPageSource(std::function<void(const std::string&)> callback);

    /**
     * @brief Capture the viewport as PNG using ICoreWebView2::CapturePreview.
     * @param file_path Destination file path.
     * @param callback Called with HRESULT on completion.
     */
    void CaptureAsPng(const std::string& file_path,
                       std::function<void(HRESULT)> callback);

    /**
     * @brief Print page to PDF using ICoreWebView2_7::PrintToPdf.
     * @param file_path Destination file path.
     * @param callback Called with HRESULT on completion.
     */
    void PrintToPdf(const std::string& file_path,
                     std::function<void(HRESULT)> callback);

    /**
     * @brief Execute Plotly.downloadImage() for Plotly chart export.
     * @param file_path Destination file path.
     * @param format "png" or "pdf".
     * @param callback Called with success/failure.
     */
    void ExportPlotly(const std::string& file_path,
                       const std::string& format,
                       std::function<void(bool)> callback);

    // ─── Scroll Preservation ─────────────────────────────────────────────

    /** @brief Save current scroll position via JS (window.scrollX/Y). */
    void SaveScrollPosition();

    /** @brief Restore previously saved scroll position after navigation. */
    void RestoreScrollPosition();

    // ─── Content Hash ────────────────────────────────────────────────────

    /** @brief Get the hash of the currently displayed content. */
    size_t GetContentHash() const;

    /** @brief Set the content hash after navigation. */
    void SetContentHash(size_t hash);

    // ─── Content ─────────────────────────────────────────────────────────

    /** @brief Get the last loaded HTML content (for PresentationBuilder). */
    std::string GetCurrentContent() const;

    // ─── Security ────────────────────────────────────────────────────────

    /**
     * @brief Apply security policy to the WebView2 controller.
     * @param dev_tools_enabled Whether to enable DevTools.
     * @param user_data_folder Allowed file:// base path.
     * @param advanced_mode Whether to allow localhost navigation.
     * @param pluto_port Pluto server port (when advanced_mode is true).
     */
    void ApplySecurityPolicy(bool dev_tools_enabled,
                              const std::string& user_data_folder,
                              bool advanced_mode = false,
                              uint16_t pluto_port = 1234);

    // ─── Callback ────────────────────────────────────────────────────────

    using WebMessageCallback = std::function<void(const std::string& viewer_id,
                                                   const std::string& json_message)>;
    void SetWebMessageCallback(WebMessageCallback callback);

    using CloseCallback = std::function<void(const std::string& viewer_id)>;
    void SetCloseCallback(CloseCallback callback);

private:
    // ─── Win32 Window Proc ───────────────────────────────────────────────

    static LRESULT CALLBACK WindowProc(HWND hwnd, UINT msg,
                                        WPARAM wParam, LPARAM lParam);
    LRESULT HandleMessage(UINT msg, WPARAM wParam, LPARAM lParam);

    void OnSize();
    void OnClose();

    // ─── WebView2 Setup ──────────────────────────────────────────────────

    void CreateWebView();
    void InjectBridgeScript();
    void SetupNavigationFilter(const std::string& user_data_folder,
                                bool advanced_mode, uint16_t pluto_port);

    // ─── Window Class Registration ───────────────────────────────────────

    static bool RegisterWindowClass();
    static bool window_class_registered_;
    static const wchar_t* WINDOW_CLASS_NAME;

    // ─── State ───────────────────────────────────────────────────────────

    HWND hwnd_;
    HWND parent_hwnd_;
    ICoreWebView2Environment* environment_;
    ICoreWebView2Controller* controller_;
    ICoreWebView2* webview_;

    std::string viewer_id_;
    std::string current_html_;
    std::string pending_html_;
    std::string pending_url_;
    std::string title_;

    size_t content_hash_ = 0;
    int saved_scroll_x_ = 0;
    int saved_scroll_y_ = 0;

    WebMessageCallback web_message_callback_;
    CloseCallback close_callback_;
};

} // namespace rj2xcl
