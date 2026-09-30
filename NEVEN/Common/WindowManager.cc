/**
 * Copyright (c) 2026 RJ2XCL Project
 */

#include "WindowManager.h"
#include "REPLManager.h"
#include "LogService.h"
#include <process.h>

namespace rj2xcl {

WindowManager::WindowManager()
    : job_handle_(0)
{}

WindowManager::~WindowManager() {
    ShutdownConsole();
}

WindowManager& WindowManager::Instance() {
    static WindowManager instance;
    return instance;
}

void WindowManager::ShowConsole() {
    REPLManager::Instance().ShowConsole();
}

void WindowManager::HideConsole() {
    REPLManager::Instance().HideConsole();

    // Return focus to Excel
    DWORD pid = _getpid();
    EnumWindows(WindowManager::FocusExcelWindowCallback, (LPARAM)pid);
}

void WindowManager::ShutdownConsole() {
    REPLManager::Instance().Shutdown();
}

BOOL CALLBACK WindowManager::FocusExcelWindowCallback(HWND hwnd, LPARAM lParam) {
    DWORD pid = (DWORD)lParam;
    DWORD window_pid;
    GetWindowThreadProcessId(hwnd, &window_pid);
    if ((pid != window_pid) || (GetWindow(hwnd, GW_OWNER) != (HWND)0) || !IsWindowVisible(hwnd))
        return TRUE;
    SetForegroundWindow(hwnd);
    SetActiveWindow(hwnd);
    SetFocus(hwnd);
    return FALSE;
}

} // namespace rj2xcl
