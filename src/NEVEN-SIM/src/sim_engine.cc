/**
 * @file sim_engine.cc
 * @brief SimEngine implementation — orchestrates the simulation pipeline.
 *
 * Copyright (c) 2026 NEVEN Project — GPL v3
 */

#include <windows.h>
#undef ERROR  // Windows macro conflicts with our enum

#include "sim_engine.h"
#include "sim_bridge.h"
#include "fit_service.h"
#include "montecarlo_service.h"
#include <thread>
#include <chrono>
#include <algorithm>

namespace neven_sim {

SimEngine& SimEngine::Instance() {
    static SimEngine instance;
    return instance;
}

SimEngine::SimEngine() {}

void SimEngine::AddAssumption(const Assumption& assumption) {
    std::lock_guard<std::mutex> lock(mutex_);
    // Replace if name already exists
    for (auto& a : assumptions_) {
        if (a.name == assumption.name) {
            a = assumption;
            return;
        }
    }
    assumptions_.push_back(assumption);
    state_ = SimState::CONFIGURING;
}

void SimEngine::RemoveAssumption(const std::string& name) {
    std::lock_guard<std::mutex> lock(mutex_);
    assumptions_.erase(
        std::remove_if(assumptions_.begin(), assumptions_.end(),
            [&name](const Assumption& a) { return a.name == name; }),
        assumptions_.end()
    );
    if (assumptions_.empty()) state_ = SimState::IDLE;
}

void SimEngine::Reset() {
    std::lock_guard<std::mutex> lock(mutex_);
    assumptions_.clear();
    sensitivity_.clear();
    summary_ = SimSummary{};
    model_function_.clear();
    last_error_.clear();
    state_ = SimState::IDLE;
}

void SimEngine::SetModelFunction(const std::string& julia_code) {
    std::lock_guard<std::mutex> lock(mutex_);
    model_function_ = julia_code;
}

void SimEngine::SetIterations(int n) {
    if (n < 1000) n = 1000;
    if (n > 10000000) n = 10000000;
    iterations_ = n;
}

void SimEngine::RunPipeline(std::function<void(bool success)> on_complete) {
    auto pipeline = [this, on_complete]() {
        // Stage 1: Fit distributions
        state_ = SimState::FITTING;
        if (!StageF_FitAll()) {
            state_ = SimState::FAILED;
            if (on_complete) on_complete(false);
            return;
        }

        // Stage 2: Run Monte Carlo
        state_ = SimState::SIMULATING;
        if (!StageS_Simulate()) {
            state_ = SimState::FAILED;
            if (on_complete) on_complete(false);
            return;
        }

        // Stage 3: Sensitivity Analysis
        state_ = SimState::ANALYZING;
        if (!StageA_Analyze()) {
            // Non-fatal — simulation results are still valid
        }

        state_ = SimState::COMPLETE;
        if (on_complete) on_complete(true);
    };

    // Phase 1: synchronous execution (called from Excel thread)
    pipeline();
}

void SimEngine::RunPipelineAsync(std::function<void(bool success)> on_complete) {
    // Phase 2: async execution on background thread (Excel won't freeze)
    auto pipeline = [this, on_complete]() {
        state_ = SimState::FITTING;
        if (!StageF_FitAll()) {
            state_ = SimState::FAILED;
            if (on_complete) on_complete(false);
            return;
        }

        state_ = SimState::SIMULATING;
        if (!StageS_Simulate()) {
            state_ = SimState::FAILED;
            if (on_complete) on_complete(false);
            return;
        }

        state_ = SimState::ANALYZING;
        if (!StageA_Analyze()) {
            // Non-fatal
        }

        state_ = SimState::COMPLETE;
        if (on_complete) on_complete(true);
    };

    std::thread(pipeline).detach();
}

bool SimEngine::FitAssumption(const std::string& assumption_name) {
    std::lock_guard<std::mutex> lock(mutex_);
    for (auto& a : assumptions_) {
        if (a.name == assumption_name) {
            std::vector<FitResult> results;
            if (FitService::FitDistributions(a.data, results)) {
                a.all_fits = results;
                if (!results.empty()) {
                    a.best_fit = results[0]; // Best by AIC
                }
                return true;
            }
            last_error_ = "Error fitting " + assumption_name;
            return false;
        }
    }
    last_error_ = "Assumption not found: " + assumption_name;
    return false;
}

bool SimEngine::StageF_FitAll() {
    for (auto& a : assumptions_) {
        if (a.data.empty()) {
            last_error_ = "No data for assumption: " + a.name;
            return false;
        }
        std::vector<FitResult> results;
        if (!FitService::FitDistributions(a.data, results)) {
            last_error_ = "Fitting failed for: " + a.name;
            return false;
        }
        a.all_fits = results;
        if (!results.empty()) {
            a.best_fit = results[0];
        } else {
            last_error_ = "No distribution fit for: " + a.name;
            return false;
        }
    }
    return true;
}

bool SimEngine::StageS_Simulate() {
    if (model_function_.empty()) {
        last_error_ = "Model function not defined";
        return false;
    }

    if (!MonteCarloService::RunSimulation(assumptions_, model_function_, iterations_, summary_)) {
        last_error_ = "Monte Carlo simulation failed in Julia";
        return false;
    }
    return true;
}

bool SimEngine::StageA_Analyze() {
    sensitivity_.clear();
    return MonteCarloService::ComputeSensitivity(assumptions_, sensitivity_);
}

std::string SimEngine::GetStateString() const {
    switch (state_.load()) {
        case SimState::IDLE:        return "Inactivo";
        case SimState::CONFIGURING: return "Configurando";
        case SimState::FITTING:     return "Ajustando distribuciones (R)";
        case SimState::SIMULATING:  return "Simulando (Julia)";
        case SimState::ANALYZING:   return "Analisis de sensibilidad";
        case SimState::COMPLETE:    return "Completo";
        case SimState::FAILED:      return "Error: " + last_error_;
        default:                    return "Desconocido";
    }
}

double SimEngine::GetPercentile(int p) const {
    if (state_ != SimState::COMPLETE) return 0.0;
    switch (p) {
        case 1:  return summary_.p1;
        case 5:  return summary_.p5;
        case 10: return summary_.p10;
        case 25: return summary_.p25;
        case 50: return summary_.p50;
        case 75: return summary_.p75;
        case 90: return summary_.p90;
        case 95: return summary_.p95;
        case 99: return summary_.p99;
        default: return summary_.p50; // Default to median
    }
}

} // namespace neven_sim
