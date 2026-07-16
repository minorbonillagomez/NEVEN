/**
 * @file sensitivity_service.cc
 * @brief SensitivityService implementation — parsing and formatting.
 *
 * Copyright (c) 2026 NEVEN Project — GPL v3
 */

#include "sensitivity_service.h"
#include "montecarlo_service.h"
#include "json11/json11.hpp"
#include <sstream>
#include <algorithm>
#include <cmath>
#include <iomanip>

namespace neven_sim {

bool SensitivityService::Compute(const std::vector<Assumption>& assumptions,
                                  std::vector<SensitivityEntry>& sensitivity) {
    return MonteCarloService::ComputeSensitivity(assumptions, sensitivity);
}

bool SensitivityService::ParseSensitivityResults(const std::string& json_str,
                                                   std::vector<SensitivityEntry>& sensitivity) {
    sensitivity.clear();

    if (json_str.empty() || json_str.find("[ERROR]") != std::string::npos) {
        return false;
    }

    std::string err;
    json11::Json json = json11::Json::parse(json_str, err);
    if (!err.empty() || !json.is_array()) return false;

    for (auto& item : json.array_items()) {
        SensitivityEntry entry;
        entry.name = item["name"].string_value();
        entry.spearman_rho = item["rho"].number_value();
        entry.contribution = item["contrib"].number_value();
        sensitivity.push_back(entry);
    }

    // Sort by absolute rho descending (Tornado chart order)
    std::sort(sensitivity.begin(), sensitivity.end(),
        [](const SensitivityEntry& a, const SensitivityEntry& b) {
            return std::abs(a.spearman_rho) > std::abs(b.spearman_rho);
        });

    return !sensitivity.empty();
}

std::string SensitivityService::FormatForExcel(const std::vector<SensitivityEntry>& sensitivity) {
    if (sensitivity.empty()) return "Sin datos de sensibilidad";

    std::ostringstream ss;
    for (size_t i = 0; i < sensitivity.size(); i++) {
        if (i > 0) ss << "; ";
        ss << sensitivity[i].name
           << ": rho=" << std::fixed << std::setprecision(3) << sensitivity[i].spearman_rho
           << " (" << (int)(sensitivity[i].contribution * 100.0 + 0.5) << "%)";
    }
    return ss.str();
}

std::string SensitivityService::FormatForWebViewer(const std::vector<SensitivityEntry>& sensitivity) {
    if (sensitivity.empty()) return "[]";

    // Build JSON for Plotly horizontal bar chart (Tornado)
    // Format: { names: [...], values: [...], contributions: [...] }
    std::ostringstream ss;
    ss << "{\"type\":\"sensitivity\",\"variables\":[";
    for (size_t i = 0; i < sensitivity.size(); i++) {
        if (i > 0) ss << ",";
        ss << "\"" << sensitivity[i].name << "\"";
    }
    ss << "],\"spearman\":[";
    for (size_t i = 0; i < sensitivity.size(); i++) {
        if (i > 0) ss << ",";
        ss << std::fixed << std::setprecision(4) << sensitivity[i].spearman_rho;
    }
    ss << "],\"contribution\":[";
    for (size_t i = 0; i < sensitivity.size(); i++) {
        if (i > 0) ss << ",";
        ss << std::fixed << std::setprecision(4) << sensitivity[i].contribution;
    }
    ss << "]}";
    return ss.str();
}

} // namespace neven_sim
