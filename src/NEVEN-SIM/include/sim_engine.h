/**
 * @file sim_engine.h
 * @brief SimEngine — central orchestrator for Monte Carlo simulations.
 *
 * Coordinates the full pipeline: data → fitting → simulation → analysis → results.
 *
 * Copyright (c) 2026 NEVEN Project — GPL v3
 */

#pragma once

#include <string>
#include <vector>
#include <mutex>
#include <atomic>
#include <functional>

namespace neven_sim {

/** @brief Simulation pipeline state machine. */
enum class SimState {
    IDLE,           ///< No simulation running
    CONFIGURING,    ///< User is defining assumptions
    FITTING,        ///< R is fitting distributions
    SIMULATING,     ///< Julia is running Monte Carlo
    ANALYZING,      ///< Computing sensitivity analysis
    COMPLETE,       ///< Results available
    FAILED          ///< Pipeline failed (renamed from ERROR to avoid Windows macro conflict)
};

/** @brief Represents a fitted distribution with parameters. */
struct FitResult {
    std::string dist_name;      // "Normal", "LogNormal", etc.
    double param1 = 0.0;        // First parameter (mean, shape, min)
    double param2 = 0.0;        // Second parameter (sd, scale, max)
    double aic = 0.0;           // Akaike Information Criterion
    double ks_p = 0.0;          // Kolmogorov-Smirnov p-value
    double ad_p = 0.0;          // Anderson-Darling p-value
};

/** @brief A single simulation assumption (input variable). */
struct Assumption {
    std::string name;           // User-friendly name
    std::string source_range;   // Excel range reference "Sheet1!A1:A1000"
    std::vector<double> data;   // Historical data values
    FitResult best_fit;         // Best-fitting distribution
    std::vector<FitResult> all_fits; // All candidate fits (ranked)
};

/** @brief Summary statistics from a simulation run. */
struct SimSummary {
    double mean = 0.0;
    double std_dev = 0.0;
    double min_val = 0.0;
    double max_val = 0.0;
    double p1 = 0.0, p5 = 0.0, p10 = 0.0, p25 = 0.0;
    double p50 = 0.0, p75 = 0.0, p90 = 0.0, p95 = 0.0, p99 = 0.0;
    int iterations = 0;
    double elapsed_ms = 0.0;
};

/** @brief Sensitivity analysis result per assumption. */
struct SensitivityEntry {
    std::string name;           // Assumption name
    double spearman_rho = 0.0;  // Spearman rank correlation
    double contribution = 0.0;  // % contribution (ρ² / Σρ²)
};

/**
 * @brief Singleton orchestrator for the simulation pipeline.
 */
class SimEngine {
public:
    static SimEngine& Instance();

    // ─── Configuration ───────────────────────────────────────────────────

    /** @brief Add an assumption to the simulation model. */
    void AddAssumption(const Assumption& assumption);

    /** @brief Remove an assumption by name. */
    void RemoveAssumption(const std::string& name);

    /** @brief Clear all assumptions and reset to IDLE state. */
    void Reset();

    /** @brief Set the model function (Julia expression). */
    void SetModelFunction(const std::string& julia_code);

    /** @brief Set number of Monte Carlo iterations. */
    void SetIterations(int n);

    // ─── Execution ───────────────────────────────────────────────────────

    /**
     * @brief Run the full simulation pipeline (synchronous — blocks caller).
     * @param on_complete Callback invoked when pipeline finishes.
     */
    void RunPipeline(std::function<void(bool success)> on_complete = nullptr);

    /**
     * @brief Run the full simulation pipeline asynchronously (background thread).
     *
     * Excel won't freeze. Check GetState() to monitor progress.
     * @param on_complete Callback invoked on the background thread when done.
     */
    void RunPipelineAsync(std::function<void(bool success)> on_complete = nullptr);

    /**
     * @brief Fit a single assumption (synchronous).
     * @param assumption_name Name of the assumption to fit.
     * @return true on success.
     */
    bool FitAssumption(const std::string& assumption_name);

    // ─── Results ─────────────────────────────────────────────────────────

    /** @brief Get current pipeline state. */
    SimState GetState() const { return state_.load(); }

    /** @brief Get state as human-readable string. */
    std::string GetStateString() const;

    /** @brief Get simulation summary (valid only in COMPLETE state). */
    const SimSummary& GetSummary() const { return summary_; }

    /** @brief Get sensitivity analysis results. */
    const std::vector<SensitivityEntry>& GetSensitivity() const { return sensitivity_; }

    /** @brief Get all configured assumptions. */
    const std::vector<Assumption>& GetAssumptions() const { return assumptions_; }

    /** @brief Get last error message (valid only in ERROR state). */
    std::string GetLastError() const { return last_error_; }

    /** @brief Get a specific percentile from last simulation (1-99). */
    double GetPercentile(int p) const;

private:
    SimEngine();
    ~SimEngine() = default;
    SimEngine(const SimEngine&) = delete;
    SimEngine& operator=(const SimEngine&) = delete;

    // Pipeline stages
    bool StageF_FitAll();
    bool StageS_Simulate();
    bool StageA_Analyze();

    // State
    std::atomic<SimState> state_{SimState::IDLE};
    std::vector<Assumption> assumptions_;
    std::string model_function_;
    int iterations_ = 1000000;
    SimSummary summary_;
    std::vector<SensitivityEntry> sensitivity_;
    std::string last_error_;
    mutable std::mutex mutex_;
};

} // namespace neven_sim
