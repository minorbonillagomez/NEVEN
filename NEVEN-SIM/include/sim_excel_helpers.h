/**
 * @file sim_excel_helpers.h
 * @brief Helper functions for Excel data extraction in NEVEN-SIM.
 *
 * Provides utilities to extract numeric data from Excel ranges (XLOPER12)
 * and convert them to std::vector<double> for the simulation pipeline.
 *
 * Copyright (c) 2026 NEVEN Project — GPL v3
 */

#pragma once

#include <vector>
#include <string>
#include "XLCALL.H"
#include "sim_engine.h"

namespace neven_sim {

/**
 * @brief Extract numeric values from an XLOPER12 (range or multi-cell array).
 * @param pxRange Pointer to the XLOPER12 from Excel.
 * @param values Output vector of extracted doubles.
 * @return true if extraction succeeded and values is non-empty.
 *
 * Handles:
 * - xltypeMulti (array from a range coerced with xlCoerce)
 * - xltypeNum (single numeric value)
 * - Skips non-numeric cells (strings, errors, blanks)
 */
bool ExtractRangeData(LPXLOPER12 pxRange, std::vector<double>& values);

/**
 * @brief Perform distribution fitting on an Excel range.
 *
 * Coerces the range, extracts data, calls FitService, and returns
 * a formatted string with the best-fit distribution.
 *
 * @param pxRange Excel range with historical data.
 * @param pxDist Optional: specific distribution name to fit (or empty for auto).
 * @return Formatted result string for the Excel cell.
 */
std::string FitRangeData(LPXLOPER12 pxRange, LPXLOPER12 pxDist);

} // namespace neven_sim
