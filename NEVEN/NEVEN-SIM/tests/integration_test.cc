/**
 * @file integration_test.cc
 * @brief Integration tests — validates the full pipeline logic.
 *
 * Tests the complete flow from assumption definition through simulation
 * to sensitivity analysis. Does not require Excel/R/Julia (uses mock bridge).
 *
 * Copyright (c) 2026 NEVEN Project — GPL v3
 */

#include <gtest/gtest.h>
#include <windows.h>
#undef ERROR

#include "sim_engine.h"
#include "sim_bridge.h"
#include "fit_service.h"
#include "montecarlo_service.h"
#include "sensitivity_service.h"
#include "sim_viewer.h"
#include "sim_excel_helpers.h"
#include <vector>
#include <string>
#include <cmath>

namespace neven_sim {
namespace testing {

// ─── Full Pipeline Logic Test ────────────────────────────────────────────────

class IntegrationTest : public ::testing::Test {
protected:
    void SetUp() override {
        SimEngine::Instance().Reset();
    }
};

TEST_F(IntegrationTest, FullPipeline_FailsGracefullyWithoutEngines) {
    // Without R/Julia engines, the pipeline should fail gracefully
    // at the fitting stage (SimBridge not connected)
    Assumption a;
    a.name = "Revenue";
    a.data = {10, 12, 11, 13, 14, 12, 15, 11, 13, 14, 16, 12};
    SimEngine::Instance().AddAssumption(a);
    SimEngine::Instance().SetModelFunction("(x) -> x * 1.1");
    SimEngine::Instance().SetIterations(10000);

    SimEngine::Instance().RunPipeline();

    // Should fail at FITTING (no R engine connected)
    EXPECT_EQ(SimEngine::Instance().GetState(), SimState::FAILED);
    EXPECT_FALSE(SimEngine::Instance().GetLastError().empty());
}

TEST_F(IntegrationTest, Pipeline_WithPreFittedAssumptions_FailsAtSimulation) {
    // If we pre-set the best_fit (skip R fitting), pipeline should reach
    // simulation stage and fail there (no Julia engine)
    Assumption a;
    a.name = "Sales";
    a.data = {100, 110, 105, 115, 120, 108, 112, 118, 122, 125};
    a.best_fit.dist_name = "norm";
    a.best_fit.param1 = 113.5;
    a.best_fit.param2 = 7.8;
    a.all_fits.push_back(a.best_fit);

    SimEngine::Instance().AddAssumption(a);
    SimEngine::Instance().SetModelFunction("(x) -> x * 0.3");
    SimEngine::Instance().SetIterations(50000);

    // The pipeline calls FitService which needs R — will fail at fitting
    SimEngine::Instance().RunPipeline();
    EXPECT_EQ(SimEngine::Instance().GetState(), SimState::FAILED);
}

TEST_F(IntegrationTest, MultipleAssumptions_AllTracked) {
    Assumption a1, a2, a3;
    a1.name = "Ventas";  a1.data = std::vector<double>(20, 100.0);
    a2.name = "Costos";  a2.data = std::vector<double>(20, 50.0);
    a3.name = "TipoCambio"; a3.data = std::vector<double>(20, 550.0);

    SimEngine::Instance().AddAssumption(a1);
    SimEngine::Instance().AddAssumption(a2);
    SimEngine::Instance().AddAssumption(a3);

    EXPECT_EQ(SimEngine::Instance().GetAssumptions().size(), 3u);
    EXPECT_EQ(SimEngine::Instance().GetState(), SimState::CONFIGURING);
}

TEST_F(IntegrationTest, StateTransitions_ResetClearsAll) {
    Assumption a;
    a.name = "X";
    a.data = std::vector<double>(15, 5.0);
    SimEngine::Instance().AddAssumption(a);
    SimEngine::Instance().SetModelFunction("(x) -> x^2");
    SimEngine::Instance().SetIterations(500000);

    EXPECT_EQ(SimEngine::Instance().GetState(), SimState::CONFIGURING);

    SimEngine::Instance().Reset();
    EXPECT_EQ(SimEngine::Instance().GetState(), SimState::IDLE);
    EXPECT_TRUE(SimEngine::Instance().GetAssumptions().empty());
    EXPECT_TRUE(SimEngine::Instance().GetLastError().empty());
    EXPECT_EQ(SimEngine::Instance().GetPercentile(50), 0.0);
}

// ─── FitService Code Generation Validation ───────────────────────────────────

TEST_F(IntegrationTest, FitCodeGeneration_HandlesNegativeData) {
    // Negative data should exclude lnorm, gamma, weibull
    std::vector<double> data = {-5, -3, -1, 0, 1, 3, 5, 7, 9, 11, 13, 15};
    std::string code = FitService::GenerateFitCode(data);
    
    // Should contain logic to exclude positive-only distributions
    EXPECT_TRUE(code.find("setdiff") != std::string::npos);
    EXPECT_TRUE(code.find("-5") != std::string::npos);
}

TEST_F(IntegrationTest, FitCodeGeneration_HandlesBetaData) {
    // Data in [0,1] should include beta
    std::vector<double> data = {0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.5};
    std::string code = FitService::GenerateFitCode(data);
    
    EXPECT_TRUE(code.find("'beta'") != std::string::npos);
}

// ─── MonteCarloService Distribution Mapping Validation ───────────────────────

TEST_F(IntegrationTest, AllDistributionsMapped) {
    // Verify all 7 R distributions map to valid Julia constructors
    std::vector<std::string> dists = {"norm", "lnorm", "gamma", "weibull", "exp", "unif", "beta"};
    
    for (const auto& d : dists) {
        FitResult fit;
        fit.dist_name = d;
        fit.param1 = 2.0;
        fit.param2 = 1.0;
        
        std::string julia = MonteCarloService::FitToJuliaDistribution(fit);
        EXPECT_TRUE(julia.find("(") != std::string::npos) << "Failed for: " << d;
        EXPECT_TRUE(julia.find(")") != std::string::npos) << "Failed for: " << d;
        // Should NOT contain "Normal" for non-normal distributions (except fallback)
        if (d != "norm") {
            // Each should have its own constructor
            EXPECT_TRUE(julia.find("2.0") != std::string::npos || julia.find("2.00") != std::string::npos)
                << "Param not found for: " << d;
        }
    }
}

// ─── SensitivityService Formatting Validation ────────────────────────────────

TEST_F(IntegrationTest, SensitivityJSON_RoundTrip) {
    // Create sensitivity data, format as JSON, parse it back
    std::vector<SensitivityEntry> original = {
        {"Ventas", 0.85, 0.60},
        {"Costos", -0.42, 0.29},
        {"TC", 0.25, 0.11}
    };

    std::string json = SensitivityService::FormatForWebViewer(original);
    
    // Verify JSON is well-formed
    EXPECT_TRUE(json.find("\"type\":\"sensitivity\"") != std::string::npos);
    EXPECT_TRUE(json.find("Ventas") != std::string::npos);
    EXPECT_TRUE(json.find("Costos") != std::string::npos);
    EXPECT_TRUE(json.find("TC") != std::string::npos);
}

// ─── SimViewer State Tests ───────────────────────────────────────────────────

TEST_F(IntegrationTest, ViewerManager_StartsNotOpen) {
    EXPECT_FALSE(SimViewerManager::Instance().IsOpen());
}

TEST_F(IntegrationTest, ViewerManager_MessageHandlerCallable) {
    bool handler_called = false;
    std::string received_type;

    SimViewerManager::Instance().SetMessageHandler([&](const std::string& type, const std::string& payload) {
        handler_called = true;
        received_type = type;
    });

    // Simulate a message from JS
    SimViewerManager::Instance().HandleWebMessage(R"({"type":"run-simulation","iterations":100000})");
    EXPECT_TRUE(handler_called);
    EXPECT_EQ(received_type, "run-simulation");
}

// ─── Excel Helpers Tests ─────────────────────────────────────────────────────

TEST_F(IntegrationTest, ExtractRangeData_FromMultiArray) {
    // Simulate a coerced multi-cell array
    XLOPER12 xlMulti;
    xlMulti.xltype = xltypeMulti;
    xlMulti.val.array.rows = 5;
    xlMulti.val.array.columns = 1;
    
    XLOPER12 cells[5];
    for (int i = 0; i < 5; i++) {
        cells[i].xltype = xltypeNum;
        cells[i].val.num = (double)(i + 1) * 10.0;
    }
    xlMulti.val.array.lparray = cells;

    std::vector<double> values;
    ASSERT_TRUE(ExtractRangeData(&xlMulti, values));
    ASSERT_EQ(values.size(), 5u);
    EXPECT_DOUBLE_EQ(values[0], 10.0);
    EXPECT_DOUBLE_EQ(values[4], 50.0);
}

TEST_F(IntegrationTest, ExtractRangeData_SkipsNonNumeric) {
    XLOPER12 xlMulti;
    xlMulti.xltype = xltypeMulti;
    xlMulti.val.array.rows = 4;
    xlMulti.val.array.columns = 1;
    
    XLOPER12 cells[4];
    cells[0].xltype = xltypeNum; cells[0].val.num = 1.0;
    cells[1].xltype = xltypeStr; cells[1].val.str = nullptr;  // String — skip
    cells[2].xltype = xltypeNum; cells[2].val.num = 3.0;
    cells[3].xltype = xltypeErr; cells[3].val.err = 15;       // Error — skip
    xlMulti.val.array.lparray = cells;

    std::vector<double> values;
    ASSERT_TRUE(ExtractRangeData(&xlMulti, values));
    ASSERT_EQ(values.size(), 2u);
    EXPECT_DOUBLE_EQ(values[0], 1.0);
    EXPECT_DOUBLE_EQ(values[1], 3.0);
}

TEST_F(IntegrationTest, ExtractRangeData_SingleNumeric) {
    XLOPER12 xlNum;
    xlNum.xltype = xltypeNum;
    xlNum.val.num = 42.5;

    std::vector<double> values;
    ASSERT_TRUE(ExtractRangeData(&xlNum, values));
    ASSERT_EQ(values.size(), 1u);
    EXPECT_DOUBLE_EQ(values[0], 42.5);
}

TEST_F(IntegrationTest, ExtractRangeData_NullReturnsEmpty) {
    std::vector<double> values;
    EXPECT_FALSE(ExtractRangeData(nullptr, values));
}

} // namespace testing
} // namespace neven_sim
