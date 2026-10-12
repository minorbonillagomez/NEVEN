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
 * NevenProgressiveRegisterExport: Declares the exported XLL function and
 * timer callback for progressive function registration.
 */

#pragma once

#include <Windows.h>

// Forward declaration of XLOPER12 for the export signature
struct xloper12;
typedef struct xloper12 XLOPER12;
typedef XLOPER12* LPXLOPER12;

namespace neven {

/**
 * @brief Starts the registration timer that periodically checks for
 * pending engine registrations and processes them on the UI thread.
 *
 * Called once during FastInit() after background threads are launched.
 * The timer fires every 100ms, checks the ProgressiveRegistrar queue,
 * and kills itself when all engines are registered.
 */
void start_registration_timer();

/**
 * @brief Timer callback — runs on UI thread.
 *
 * Checks the ProgressiveRegistrar for pending registrations and
 * processes them. Kills the timer when all engines are complete.
 */
void CALLBACK registration_timer_proc(HWND hwnd, UINT msg, UINT_PTR timer_id, DWORD tick);

} // namespace neven

/**
 * @brief Exported XLL function callable via xlcOnTime for progressive registration.
 *
 * This function is exported in the .def file so Excel can call it.
 * It delegates to ProgressiveRegistrar::ProcessPendingRegistrations().
 *
 * @return LPXLOPER12 Always returns xltypeNil (return value ignored by xlcOnTime).
 */
extern "C" __declspec(dllexport) LPXLOPER12 WINAPI NEVEN_ProgressiveRegister(void);
