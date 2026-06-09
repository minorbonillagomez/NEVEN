/**
 * Copyright (c) 2026 RJ2XCL Project
 *
 * This file is part of RJ2XCL.
 */

#include "stdafx.h"
#include "WinExcelBridge.h"
#include <stdarg.h>

namespace rj2xcl {

  int WinExcelBridge::Excel12(int xlfn, LPXLOPER12 operRes, int count, ...) {
    LPXLOPER12 rgOper[32]; // Max 32 arguments as per Excel SDK
    va_list ap;
    va_start(ap, count);
    for (int i = 0; i < count && i < 32; i++) {
      rgOper[i] = va_arg(ap, LPXLOPER12);
    }
    va_end(ap);

    // Call the real Excel12v (which is linked via stubs or lib)
    return ::Excel12v(xlfn, operRes, count, rgOper);
  }

  int WinExcelBridge::Excel12v(int xlfn, LPXLOPER12 operRes, int count, LPXLOPER12 opers[]) {
    return ::Excel12v(xlfn, operRes, count, opers);
  }

} // namespace rj2xcl
