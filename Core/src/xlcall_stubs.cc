/**
 * Copyright (c) 2026 RJ2XCL Project
 *
 * Stub implementations for Excel SDK functions.
 * 
 * MdCallBack12 signature (from Excel SDK):
 *   int pascal MdCallBack12(int xlfn, int coper, LPXLOPER12 *rgpxloper12, LPXLOPER12 xloper12Res);
 *
 * Note: parameter order is xlfn, count, opers[], operRes — NOT xlfn, operRes, count, opers[]
 */

#include <windows.h>
#include <stdarg.h>
#include "XLCALL.h"

// MdCallBack12 real signature: (int xlfn, int coper, LPXLOPER12 *rgpxloper12, LPXLOPER12 xloper12Res)
typedef int (PASCAL *MDCALLBACK12PROC)(int xlfn, int coper, LPXLOPER12 *rgpxloper12, LPXLOPER12 xloper12Res);
static MDCALLBACK12PROC g_pMdCallBack12 = NULL;

extern "C" {

int pascal Excel12(int xlfn, LPXLOPER12 operRes, int count, ...) {
    if (!g_pMdCallBack12) return 0x03FF;
    
    LPXLOPER12 rgOper[32];
    va_list ap;
    va_start(ap, count);
    for (int i = 0; i < count && i < 32; i++) {
        rgOper[i] = va_arg(ap, LPXLOPER12);
    }
    va_end(ap);
    
    return g_pMdCallBack12(xlfn, count, rgOper, operRes);
}

int pascal Excel12v(int xlfn, LPXLOPER12 operRes, int count, LPXLOPER12 opers[]) {
    if (!g_pMdCallBack12) return 0x03FF;
    return g_pMdCallBack12(xlfn, count, opers, operRes);
}

void SetExcel12EntryPt(MDCALLBACK12PROC pMdCallBack12) {
    g_pMdCallBack12 = pMdCallBack12;
}

} // extern "C"
