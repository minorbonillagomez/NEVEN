/**
 * @file fit_service.h
 * @brief FitService — distribution fitting via R engine.
 *
 * Generates R code for fitdistrplus, sends via SimBridge, and parses results.
 *
 * Copyright (c) 2026 NEVEN Project — GPL v3
 */

#pragma once

#include <string>
#include <vector>
#include "sim_engine.h"

namespace neven_sim {

/**
 * @brief Service for fitting statistical distributions to data using R.
 *
 * Supports: Normal, LogNormal, Gamma, Weibull, Exponential, Uniform, Beta.
 * Uses R packages: fitdistrplus, MASS.
 */
class FitService {
public:
    /**
     * @brief Fit candidate distributions to a data vector.
     * @param data Historical data points.
     * @param results Output vector of FitResult (ranked by AIC).
     * @return true on success, false if R call failed.
     */
    static bool FitDistributions(const std::vector<double>& data,
                                  std::vector<FitResult>& results);

    /**
     * @brief Fit a specific distribution to data.
     * @param data Historical data points.
     * @param dist_name Distribution name (e.g., "norm", "lnorm").
     * @param result Output FitResult with parameters and GoF stats.
     * @return true on success.
     */
    static bool FitSpecific(const std::vector<double>& data,
                            const std::string& dist_name,
                            FitResult& result);

    /**
     * @brief Check if fitdistrplus is available in R.
     * @return true if the package is installed.
     */
    static bool CheckDependencies();

    // ─── Internal (public for testability — class is stateless) ──────────

    /**
     * @brief Generate R code string for fitting all candidates.
     * @param data Data vector to embed in the R code.
     * @return Complete R code string.
     */
    static std::string GenerateFitCode(const std::vector<double>& data);

    /**
     * @brief Parse JSON result from R into FitResult vector.
     * @param json_str JSON string returned by R.
     * @param results Output vector (sorted by AIC ascending).
     * @return true if parsing succeeded.
     */
    static bool ParseFitResults(const std::string& json_str,
                                std::vector<FitResult>& results);
};

} // namespace neven_sim
