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

#include <string>
#include <vector>
#include <sstream>

/**
 * @brief String utility functions for splitting, trimming, and conversion.
 *
 * Provides static helper methods for common string operations used
 * throughout the RJ2XCL codebase, particularly for Windows path handling.
 */
class StringUtilities {

public:

  /**
   * @brief Checks if a string ends with a given suffix.
   * @param fullString The string to check.
   * @param ending The suffix to look for.
   * @return true if fullString ends with ending.
   */
  static bool EndsWith(std::string const &fullString, std::string const &ending) {
    if (fullString.length() >= ending.length()) {
      return (0 == fullString.compare(fullString.length() - ending.length(), ending.length(), ending));
    }
    else {
      return false;
    }
  }

  /**
   * @brief Case-insensitive string comparison for Windows paths.
   * @param a First string.
   * @param b Second string.
   * @return 0 if equal (ignoring case), non-zero otherwise.
   */
  static int ICaseCompare(const std::string &a, const std::string &b) {
    size_t len = a.length();
    if (len != b.length()) return 1;
    for (size_t i = 0; i < len; i++) {
      if (toupper(a[i]) != toupper(b[i])) return 2;
    }
    return 0;
  }
  
  /**
   * @brief Escapes backslashes by doubling them.
   * @param str Input string containing single backslashes.
   * @return New string with all backslashes doubled.
   */
  static std::string EscapeBackslashes(const std::string &str) {

    std::stringstream new_string;
    std::stringstream old_string(str);
    std::string part;

    while (std::getline(old_string, part, '\\'))
    {
      new_string << part;
      if (!old_string.eof()) new_string << "\\\\";
    }

    return new_string.str();
  }

  /**
   * @brief Trims leading and trailing whitespace characters from a string.
   * @param str Input string to trim.
   * @param whitespace Characters to consider as whitespace (default: space, CR, LF, tab).
   * @return Trimmed string, or empty string if input is all whitespace.
   */
  static std::string Trim(const std::string& str, const std::string& whitespace = " \r\n\t")
  {
    const auto strBegin = str.find_first_not_of(whitespace);
    if (strBegin == std::string::npos)
      return ""; // no content

    const auto strEnd = str.find_last_not_of(whitespace);
    const auto strRange = strEnd - strBegin + 1;

    return str.substr(strBegin, strRange);
  }

  /**
   * @brief Splits a string by a delimiter into a vector of substrings.
   * @param s Input string to split.
   * @param delim Delimiter character.
   * @param minLength Minimum length for a substring to be included.
   * @param elems Output vector to append results to.
   * @param ftrim If true, trims whitespace from each element.
   * @return Reference to the output vector.
   */
  static std::vector<std::string> &Split(const std::string &s, char delim, int minLength, std::vector<std::string> &elems, bool ftrim = false)
  {
    std::stringstream ss(s);
    std::string item;
    while (std::getline(ss, item, delim))
    {
      if (ftrim) item = Trim(item);
      if (!item.empty() && item.length() >= minLength) elems.push_back(item);
    }
    return elems;
  }
};
