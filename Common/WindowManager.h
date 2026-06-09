/**
 * Copyright (c) 2026 RJ2XCL Project
 */

#pragma once

#include <windows.h>
#include <string>

namespace rj2xcl {

/**
 * @brief Manages the console window lifecycle.
 *
 * Delegates to REPLManager for the WebView2-based REPL console.
 * Retains the FocusExcelWindowCallback for returning focus to Excel.
 */
class WindowManager {
public:
    /** @brief Returns the singleton instance of WindowManager. */
    static WindowManager& Instance();

    /** @brief Opens or brings to front the REPL console window. */
    void ShowConsole();

    /** @brief Hides the REPL console window and returns focus to Excel. */
    void HideConsole();

    /** @brief Closes the console and releases all associated resources. */
    void ShutdownConsole();

    /**
     * @brief Sets the Windows Job Object handle for child process management.
     * @param hJob Handle to the Job Object.
     */
    void SetJobHandle(HANDLE hJob) { job_handle_ = hJob; }

private:
    WindowManager();
    ~WindowManager();
    WindowManager(const WindowManager&) = delete;
    WindowManager& operator=(const WindowManager&) = delete;

    static BOOL CALLBACK FocusExcelWindowCallback(HWND hwnd, LPARAM lParam);

    HANDLE job_handle_;
};

} // namespace rj2xcl
