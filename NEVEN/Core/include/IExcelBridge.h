/**
 * Copyright (c) 2026 RJ2XCL Project
 *
 * This file is part of RJ2XCL.
 *
 * RJ2XCL is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 */

#pragma once

#include <windows.h>
#include "XLCALL.h"

namespace rj2xcl {

  /**
   * @brief Interface for Excel SDK abstraction.
   * 
   * This interface allows the engine to interact with Excel without
   * direct dependency on the host process during testing.
   */
  class IExcelBridge {
  public:
    virtual ~IExcelBridge() = default;

    /**
     * @brief Wrapper for the Excel12 function.
     */
    virtual int Excel12(int xlfn, LPXLOPER12 operRes, int count, ...) = 0;

    /**
     * @brief Wrapper for the Excel12v function.
     */
    virtual int Excel12v(int xlfn, LPXLOPER12 operRes, int count, LPXLOPER12 opers[]) = 0;
  };

} // namespace rj2xcl
