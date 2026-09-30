/**
 * Copyright (c) 2026 NEVEN Project
 *
 * This file is part of NEVEN.
 *
 * NEVEN is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 */

#include "NevenProgressiveRegisterExport.h"
#include "NevenProgressiveRegistrar.h"
#include "LogService.h"
#include "XLCALL.h"

namespace {
    /// Timer ID for the registration timer (0 = not active)
    UINT_PTR g_registration_timer_id = 0;
} // anonymous namespace

namespace neven {

void start_registration_timer() {
    // Start a timer that fires every 500ms on the UI thread.
    // Using 500ms instead of 100ms to reduce interference with Excel's
    // initialization and the Ribbon COM add-in's OnConnection sequence.
    // The first fire is also delayed by 500ms to let xlAutoOpen complete.
    g_registration_timer_id = SetTimer(NULL, 0, 500, registration_timer_proc);
    if (g_registration_timer_id == 0) {
        RJ2XCL_LOG_ERR("ProgressiveRegister: failed to create registration timer");
    } else {
        RJ2XCL_LOG_INFO("ProgressiveRegister: registration timer started (id=%llu, interval=500ms)",
                        static_cast<unsigned long long>(g_registration_timer_id));
    }
}

void CALLBACK registration_timer_proc(HWND /*hwnd*/, UINT /*msg*/, UINT_PTR timer_id, DWORD /*tick*/) {
    auto& registrar = ProgressiveRegistrar::Instance();

    if (registrar.HasPending()) {
        registrar.ProcessPendingRegistrations();
    }

    if (registrar.AllComplete()) {
        RJ2XCL_LOG_INFO("ProgressiveRegister: all engines registered, killing timer");
        KillTimer(NULL, timer_id);
        g_registration_timer_id = 0;
    }
}

} // namespace neven

extern "C" __declspec(dllexport) LPXLOPER12 WINAPI NEVEN_ProgressiveRegister(void) {
    neven::ProgressiveRegistrar::Instance().ProcessPendingRegistrations();

    // Return xltypeNil — value is ignored by xlcOnTime
    static XLOPER12 result;
    result.xltype = xltypeNil;
    return &result;
}
