/**
 * Copyright (c) 2026 RJ2XCL Project
 * 
 * This file is part of RJ2XCL.
 *
 * RJ2XCL is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * RJ2XCL is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with RJ2XCL.  If not, see <http://www.gnu.org/licenses/>.
 */

#pragma once

#include <iostream>
#include <sstream>
#include <windows.h>

#ifdef _DEBUG

/**
 * @brief Printf-style debug output to the Visual Studio Output window.
 *
 * Only available in debug builds. Removed by preprocessor in release.
 * @param fmt Printf-style format string.
 * @return Number of characters written.
 */
int DebugOut(const char *fmt, ...);

/**
 * @brief Stream buffer that redirects output to OutputDebugStringA.
 *
 * Allows using std::cout/std::cerr in non-console applications by
 * routing output to the Visual Studio debugger output window.
 * Only active in debug builds.
 */
class dbg_stream_for_stdio : public std::stringbuf
{
public:
  /**
   * @brief Constructs the debug stream buffer.
   * @param prefix Optional prefix for output lines (currently unused).
   */
  dbg_stream_for_stdio(const std::string &prefix = "") {}
  ~dbg_stream_for_stdio() { sync(); }

  /**
   * @brief Flushes buffered content to OutputDebugStringA.
   * @return 0 on success.
   */
  int sync()
  {
    ::OutputDebugStringA(str().c_str());
    str(std::string()); 
    return 0;
  }
public:
  /** @brief Redirects std::cout and std::cerr to debug output. */
  static void InitStreams();
};

#else 
#define DebugOut(fmt, ...){}
#endif

