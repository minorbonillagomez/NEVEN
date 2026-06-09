/**
 * Copyright (c) 2026 RJ2XCL Project
 *
 * This file is part of RJ2XCL.
 */

#pragma once

#include "IExcelBridge.h"

namespace rj2xcl {

  /**
   * @brief Windows implementation of IExcelBridge using the real Excel SDK.
   */
  class WinExcelBridge : public IExcelBridge {
  public:
    WinExcelBridge() = default;
    virtual ~WinExcelBridge() = default;

    virtual int Excel12(int xlfn, LPXLOPER12 operRes, int count, ...) override;
    virtual int Excel12v(int xlfn, LPXLOPER12 operRes, int count, LPXLOPER12 opers[]) override;

  private:
    // Prevent copying
    WinExcelBridge(const WinExcelBridge&) = delete;
    WinExcelBridge& operator=(const WinExcelBridge&) = delete;
  };

} // namespace rj2xcl
