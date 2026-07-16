/**
 * @file sensitivity_service.h
 * @brief SensitivityService — Spearman rank correlation analysis.
 *
 * Computes sensitivity (Tornado chart data) from simulation results.
 * Delegates heavy computation to Julia via MonteCarloService.
 *
 * Copyright (c) 2026 NEVEN Project — GPL v3
 */

#pragma once

#include <string>
#include <vector>
#include "sim_engine.h"

namespace neven_sim {

/**
 * @brief Service for sensitivity analysis (Spearman rank correlation).
 *
 * Computes how much each input assumption contributes to output variance.
 * Results are sorted by |ρ| descending (Tornado chart order).
 */
class SensitivityService {
public:
    /**
     * @brief Compute Spearman rank correlation from last simulation.
     * @param assumptions The assumptions used (for names).
     * @param sensitivity Output vector sorted by |ρ| descending.
     * @return true on success.
     */
    static bool Compute(const std::vector<Assumption>& assumptions,
                        std::vector<SensitivityEntry>& sensitivity);

    /**
     * @brief Parse a JSON sensitivity response from Julia.
     * @param json_str JSON array string from Julia.
     * @param sensitivity Output vector.
     * @return true if parsing succeeded and results are non-empty.
     */
    static bool ParseSensitivityResults(const std::string& json_str,
                                         std::vector<SensitivityEntry>& sensitivity);

    /**
     * @brief Format sensitivity results as a display string for Excel.
     * @param sensitivity The computed sensitivity entries.
     * @return Formatted string "Name: ρ=X.XX (YY%); ..."
     */
    static std::string FormatForExcel(const std::vector<SensitivityEntry>& sensitivity);

    /**
     * @brief Format sensitivity results as JSON for WebViewer.
     * @param sensitivity The computed sensitivity entries.
     * @return JSON string for Plotly Tornado chart.
     */
    static std::string FormatForWebViewer(const std::vector<SensitivityEntry>& sensitivity);
};

} // namespace neven_sim
