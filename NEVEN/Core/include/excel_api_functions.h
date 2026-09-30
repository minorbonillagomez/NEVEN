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

/**
 * @brief Registers all static Excel functions (basic_functions + language calls).
 *
 * Called from xlAutoOpen after initialization completes.
 */
void RegisterFunctions();

/**
 * @brief Removes registered functions from Excel's function wizard.
 *
 * Called before re-registering during UpdateFunctions().
 * Safe to call with no registered functions.
 */
void UnregisterFunctions();

/**
 * @brief Registers the "NEVEN.Exec.X" and "NEVEN.Call.X" functions for a language.
 * @param language_name Display name of the language (e.g., "R", "Julia").
 * @param language_key Numeric key identifying the language service.
 * @param generic If true, registers generic (non-language-specific) variants.
 * @return true if registration succeeded.
 */
bool ExcelRegisterLanguageCalls(const char *language_name, uint32_t language_key, bool generic = false);

