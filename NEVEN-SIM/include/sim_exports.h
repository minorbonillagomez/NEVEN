/**
 * @file sim_exports.h
 * @brief XLL entry points and worksheet function exports for NEVEN-SIM.
 *
 * Copyright (c) 2026 NEVEN Project — GPL v3
 */

#pragma once

#include "XLCALL.H"

// ─── XLL Lifecycle ───────────────────────────────────────────────────────────

extern "C" {
    __declspec(dllexport) int __stdcall xlAutoOpen(void);
    __declspec(dllexport) int __stdcall xlAutoClose(void);
    __declspec(dllexport) void __stdcall xlAutoFree12(LPXLOPER12 px);
    __declspec(dllexport) LPXLOPER12 __stdcall xlAddInManagerInfo12(LPXLOPER12 pxAction);
}

// ─── Worksheet Functions ─────────────────────────────────────────────────────

extern "C" {
    __declspec(dllexport) LPXLOPER12 __stdcall SIM_Workspace(void);
    __declspec(dllexport) LPXLOPER12 __stdcall SIM_Fit(LPXLOPER12 pxRange, LPXLOPER12 pxDist);
    __declspec(dllexport) LPXLOPER12 __stdcall SIM_Run(LPXLOPER12 pxIterations);
    __declspec(dllexport) LPXLOPER12 __stdcall SIM_QuickRun(LPXLOPER12 pxRange, LPXLOPER12 pxModel, LPXLOPER12 pxIterations);
    __declspec(dllexport) LPXLOPER12 __stdcall SIM_Datos(LPXLOPER12 pxN);
    __declspec(dllexport) LPXLOPER12 __stdcall SIM_Exportar(void);
    __declspec(dllexport) LPXLOPER12 __stdcall SIM_Percentile(LPXLOPER12 pxP);
    __declspec(dllexport) LPXLOPER12 __stdcall SIM_Sensitivity(void);
    __declspec(dllexport) LPXLOPER12 __stdcall SIM_Status(void);
}
