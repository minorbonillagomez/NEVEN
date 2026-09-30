/**
 * @file montecarlo_service.h
 * @brief MonteCarloService — Julia-based Monte Carlo simulation engine.
 *
 * Generates Julia code for sampling from fitted distributions and evaluating
 * a user-defined model function across N iterations.
 *
 * Copyright (c) 2026 NEVEN Project — GPL v3
 */

#pragma once

#include <string>
#include <vector>
#include "sim_engine.h"

namespace neven_sim {

/**
 * @brief Service for running Monte Carlo simulations in Julia.
 *
 * Requires: Distributions.jl in Julia environment.
 * Uses Julia threads for parallel evaluation when available.
 */
class MonteCarloService {
public:
    /**
     * @brief Run a Monte Carlo simulation with the given assumptions and model.
     * @param assumptions Vector of assumptions with fitted distributions.
     * @param model_function Julia expression (function of assumption variables).
     * @param iterations Number of iterations (10,000 to 10,000,000).
     * @param summary Output summary statistics.
     * @return true on success.
     */
    static bool RunSimulation(const std::vector<Assumption>& assumptions,
                              const std::string& model_function,
                              int iterations,
                              SimSummary& summary);

    /**
     * @brief Compute sensitivity (Spearman rank correlation) for last simulation.
     * @param assumptions The assumptions used in the simulation.
     * @param sensitivity Output sensitivity entries.
     * @return true on success.
     */
    static bool ComputeSensitivity(const std::vector<Assumption>& assumptions,
                                    std::vector<SensitivityEntry>& sensitivity);

    /**
     * @brief Check if Distributions.jl is available in Julia.
     * @return true if the package is installed.
     */
    static bool CheckDependencies();

    /**
     * @brief Load the NEVENSim.jl module into the Julia runtime.
     * @return true on success.
     */
    static bool LoadSimModule();

    // ─── Internal (public for testability — class is stateless) ──────────

    /**
     * @brief Generate Julia code for the Monte Carlo simulation.
     * @param assumptions Assumptions with distributions.
     * @param model_function User model expression.
     * @param iterations Number of iterations.
     * @return Complete Julia code string.
     */
    static std::string GenerateSimCode(const std::vector<Assumption>& assumptions,
                                        const std::string& model_function,
                                        int iterations);

    /**
     * @brief Map FitResult distribution name to Julia Distributions.jl constructor.
     * @param fit The fitted distribution.
     * @return Julia expression like "Normal(5.2, 1.3)".
     */
    static std::string FitToJuliaDistribution(const FitResult& fit);
};

} // namespace neven_sim
