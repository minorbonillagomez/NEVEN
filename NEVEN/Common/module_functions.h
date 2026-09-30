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

#include <Windows.h>
#include <Shlwapi.h>

#include <string>
#include <vector>

#define DEFAULT_BASE_KEY        HKEY_CURRENT_USER
#define DEFAULT_REGISTRY_KEY    "Software\\RJ2XCL"

#define PATH_PATH_SEPARATOR ";"

namespace ModuleFunctions {

  /**
   * @brief Reads a string resource embedded in the current DLL.
   * @param resource_id Resource identifier (MAKEINTRESOURCE or string name).
   * @return Resource content as a UTF-8 string, or empty on failure.
   */
  std::string ReadResource(LPTSTR resource_id);

  /**
   * @brief Returns the directory path of the current module (DLL).
   * @return Absolute path to the directory containing this DLL.
   */
  std::string ModulePath();

}
