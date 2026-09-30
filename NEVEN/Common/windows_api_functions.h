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

#include "result.h"

namespace APIFunctions {

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

  /** @brief Error codes for file operations. */
  typedef enum {
    Success = 0,        ///< Operation completed successfully
    FileNotFound = 1,   ///< File does not exist at the given path
    FileReadError = 2,  ///< File exists but could not be read
    ParseError = 3      ///< File was read but content could not be parsed
  } 
  FileError;

  /**
   * @brief Lists files in a directory with their last-write timestamps.
   *
   * Returns only files (not subdirectories). Each entry contains the
   * full absolute path and the FILETIME of the last modification.
   *
   * @param directory Absolute path to the directory to list.
   * @return Vector of (full_path, last_write_time) pairs.
   */
  std::vector<std::pair<std::string, FILETIME>> ListDirectory(const std::string &directory);

  /**
   * @brief Reads a string value from the Windows Registry.
   * @param result_value Output: the registry string value.
   * @param name Name of the registry value to read.
   * @param key Registry subkey path (defaults to "Software\\RJ2XCL").
   * @param base_key Base registry key (defaults to HKEY_CURRENT_USER).
   * @return true if the value was read successfully.
   */
  bool GetRegistryString(std::string &result_value, const char *name, const char *key = 0, HKEY base_key = 0);

  /**
   * @brief Reads a DWORD value from the Windows Registry.
   * @param result_value Output: the registry DWORD value.
   * @param name Name of the registry value to read.
   * @param key Registry subkey path (defaults to "Software\\RJ2XCL").
   * @param base_key Base registry key (defaults to HKEY_CURRENT_USER).
   * @return true if the value was read successfully.
   */
  bool GetRegistryDWORD(DWORD &result_value, const char *name, const char *key = 0, HKEY base_key = 0);

  /**
   * @brief Returns the current process PATH environment variable.
   *
   * Caches the original PATH on first call for later restoration.
   * @return Current PATH string.
   */
  std::string GetPath();

  /**
   * @brief Appends a directory to the end of the process PATH.
   * @param new_path Directory path to append.
   * @return The updated PATH string.
   */
  std::string AppendPath(const std::string &new_path);

  /**
   * @brief Prepends a directory to the beginning of the process PATH.
   * @param new_path Directory path to prepend.
   * @return The updated PATH string.
   */
  std::string PrependPath(const std::string &new_path);

  /**
   * @brief Sets the process PATH environment variable directly.
   * @param path New PATH value to set.
   */
  void SetPath(const std::string &path);

  /**
   * @brief Reads a file and returns its contents as a string.
   * @param path Absolute path to the file.
   * @return Result containing file contents on success, or FileError on failure.
   */
  rj2xcl::Result<std::string, FileError> FileContents(const std::string &path);

};
