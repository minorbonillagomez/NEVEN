/**
 * @file montecarlo_test.cc
 * @brief Unit tests for MonteCarloService — validates code generation and distribution mapping.
 *
 * Tests Julia code generation and FitResult → Distributions.jl mapping
 * without requiring Julia to be running.
 *
 * Copyright (c) 2026 NEVEN Project — GPL v3
 */

#include <gtest/gtest.h>
#include <windows.h>
#undef ERROR
#include "montecarlo_service.h"
#include <string>
#include <vector>

namespace neven_sim {
namespace testing {

// ─── Distribution Mapping Tests ──────────────────────────────────────────────

TEST(MonteCarloServiceTest, FitToJulia_Normal) {
    FitResult fit;
    fit.dist_name = "norm";
    fit.param1 = 5.2;
    fit.param2 = 1.3;
    std::string result = MonteCarloService::FitToJuliaDistribution(fit);
    EXPECT_TRUE(result.find("Normal(") == 0);
    EXPECT_TRUE(result.find("5.2") != std::string::npos);
    EXPECT_TRUE(result.find("1.3") != std::string::npos);
}

TEST(MonteCarloServiceTest, FitToJulia_LogNormal) {
    FitResult fit;
    fit.dist_name = "lnorm";
    fit.param1 = 1.6;
    fit.param2 = 0.3;
    std::string result = MonteCarloService::FitToJuliaDistribution(fit);
    EXPECT_TRUE(result.find("LogNormal(") == 0);
    EXPECT_TRUE(result.find("1.6") != std::string::npos);
}

TEST(MonteCarloServiceTest, FitToJulia_Gamma) {
    FitResult fit;
    fit.dist_name = "gamma";
    fit.param1 = 3.0;
    fit.param2 = 0.6;
    std::string result = MonteCarloService::FitToJuliaDistribution(fit);
    EXPECT_TRUE(result.find("Gamma(") == 0);
}

TEST(MonteCarloServiceTest, FitToJulia_Weibull) {
    FitResult fit;
    fit.dist_name = "weibull";
    fit.param1 = 2.0;
    fit.param2 = 5.0;
    std::string result = MonteCarloService::FitToJuliaDistribution(fit);
    EXPECT_TRUE(result.find("Weibull(") == 0);
}

TEST(MonteCarloServiceTest, FitToJulia_Exponential) {
    FitResult fit;
    fit.dist_name = "exp";
    fit.param1 = 0.5;
    fit.param2 = 0.0;
    std::string result = MonteCarloService::FitToJuliaDistribution(fit);
    EXPECT_TRUE(result.find("Exponential(") == 0);
    EXPECT_TRUE(result.find("0.5") != std::string::npos);
}

TEST(MonteCarloServiceTest, FitToJulia_Uniform) {
    FitResult fit;
    fit.dist_name = "unif";
    fit.param1 = 10.0;
    fit.param2 = 50.0;
    std::string result = MonteCarloService::FitToJuliaDistribution(fit);
    EXPECT_TRUE(result.find("Uniform(") == 0);
}

TEST(MonteCarloServiceTest, FitToJulia_Beta) {
    FitResult fit;
    fit.dist_name = "beta";
    fit.param1 = 2.0;
    fit.param2 = 5.0;
    std::string result = MonteCarloService::FitToJuliaDistribution(fit);
    EXPECT_TRUE(result.find("Beta(") == 0);
}

TEST(MonteCarloServiceTest, FitToJulia_UnknownFallsBackToNormal) {
    FitResult fit;
    fit.dist_name = "unknown_dist";
    fit.param1 = 1.0;
    fit.param2 = 2.0;
    std::string result = MonteCarloService::FitToJuliaDistribution(fit);
    EXPECT_TRUE(result.find("Normal(") == 0);
}

// ─── Code Generation Tests ───────────────────────────────────────────────────

TEST(MonteCarloServiceTest, GenerateCode_ContainsDistributions) {
    Assumption a1;
    a1.name = "Ventas";
    a1.best_fit.dist_name = "norm";
    a1.best_fit.param1 = 100.0;
    a1.best_fit.param2 = 15.0;

    Assumption a2;
    a2.name = "Costos";
    a2.best_fit.dist_name = "lnorm";
    a2.best_fit.param1 = 3.5;
    a2.best_fit.param2 = 0.4;

    std::vector<Assumption> assumptions = {a1, a2};
    std::string code = MonteCarloService::GenerateSimCode(assumptions, "(v, c) -> v - c", 100000);

    EXPECT_TRUE(code.find("Normal(") != std::string::npos);
    EXPECT_TRUE(code.find("LogNormal(") != std::string::npos);
    EXPECT_TRUE(code.find("100000") != std::string::npos);
    EXPECT_TRUE(code.find("n_vars = 2") != std::string::npos);
}

TEST(MonteCarloServiceTest, GenerateCode_ContainsModelFunction) {
    Assumption a;
    a.name = "X";
    a.best_fit.dist_name = "norm";
    a.best_fit.param1 = 0.0;
    a.best_fit.param2 = 1.0;

    std::vector<Assumption> assumptions = {a};
    std::string model = "(x) -> x^2";
    std::string code = MonteCarloService::GenerateSimCode(assumptions, model, 10000);

    EXPECT_TRUE(code.find("(x) -> x^2") != std::string::npos);
}

TEST(MonteCarloServiceTest, GenerateCode_ContainsStatisticsAndJSON) {
    Assumption a;
    a.name = "X";
    a.best_fit.dist_name = "unif";
    a.best_fit.param1 = 0.0;
    a.best_fit.param2 = 1.0;

    std::vector<Assumption> assumptions = {a};
    std::string code = MonteCarloService::GenerateSimCode(assumptions, "(x) -> x", 1000);

    // Should contain percentile calculation
    EXPECT_TRUE(code.find("pct(") != std::string::npos);
    // Should contain JSON output
    EXPECT_TRUE(code.find("mean") != std::string::npos);
    EXPECT_TRUE(code.find("p50") != std::string::npos);
    EXPECT_TRUE(code.find("p95") != std::string::npos);
}

TEST(MonteCarloServiceTest, GenerateCode_StoresGlobalForSensitivity) {
    Assumption a;
    a.name = "X";
    a.best_fit.dist_name = "norm";
    a.best_fit.param1 = 0.0;
    a.best_fit.param2 = 1.0;

    std::vector<Assumption> assumptions = {a};
    std::string code = MonteCarloService::GenerateSimCode(assumptions, "(x) -> x", 1000);

    EXPECT_TRUE(code.find("_sim_samples") != std::string::npos);
    EXPECT_TRUE(code.find("_sim_results") != std::string::npos);
}

TEST(MonteCarloServiceTest, GenerateCode_MultipleAssumptionsCorrectIndexing) {
    Assumption a1, a2, a3;
    a1.name = "A"; a1.best_fit.dist_name = "norm"; a1.best_fit.param1 = 1; a1.best_fit.param2 = 1;
    a2.name = "B"; a2.best_fit.dist_name = "norm"; a2.best_fit.param1 = 2; a2.best_fit.param2 = 1;
    a3.name = "C"; a3.best_fit.dist_name = "norm"; a3.best_fit.param1 = 3; a3.best_fit.param2 = 1;

    std::vector<Assumption> assumptions = {a1, a2, a3};
    std::string code = MonteCarloService::GenerateSimCode(assumptions, "(a,b,c) -> a+b+c", 5000);

    // Should reference samples[i, 1], samples[i, 2], samples[i, 3]
    EXPECT_TRUE(code.find("samples[i, 1]") != std::string::npos);
    EXPECT_TRUE(code.find("samples[i, 2]") != std::string::npos);
    EXPECT_TRUE(code.find("samples[i, 3]") != std::string::npos);
    EXPECT_TRUE(code.find("n_vars = 3") != std::string::npos);
}

// ─── RunSimulation Input Validation ──────────────────────────────────────────

TEST(MonteCarloServiceTest, RunSimulation_EmptyAssumptionsReturnsFalse) {
    std::vector<Assumption> empty;
    SimSummary summary;
    EXPECT_FALSE(MonteCarloService::RunSimulation(empty, "(x)->x", 1000, summary));
}

TEST(MonteCarloServiceTest, ComputeSensitivity_EmptyAssumptionsReturnsFalse) {
    std::vector<Assumption> empty;
    std::vector<SensitivityEntry> sensitivity;
    EXPECT_FALSE(MonteCarloService::ComputeSensitivity(empty, sensitivity));
}

} // namespace testing
} // namespace neven_sim
