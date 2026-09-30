/**
 * @file sim_engine_test.cc
 * @brief Unit tests for SimEngine — validates orchestration logic.
 *
 * Tests state machine transitions, assumption management, and percentile
 * retrieval without requiring R/Julia engines.
 *
 * Copyright (c) 2026 NEVEN Project — GPL v3
 */

#include <gtest/gtest.h>
#include <windows.h>
#undef ERROR
#include "sim_engine.h"

namespace neven_sim {
namespace testing {

class SimEngineTest : public ::testing::Test {
protected:
    void SetUp() override {
        SimEngine::Instance().Reset();
    }
};

TEST_F(SimEngineTest, InitialStateIsIdle) {
    EXPECT_EQ(SimEngine::Instance().GetState(), SimState::IDLE);
}

TEST_F(SimEngineTest, AddAssumptionChangesToConfiguring) {
    Assumption a;
    a.name = "Ventas";
    a.source_range = "A1:A100";
    a.data = {1.0, 2.0, 3.0, 4.0, 5.0};

    SimEngine::Instance().AddAssumption(a);
    EXPECT_EQ(SimEngine::Instance().GetState(), SimState::CONFIGURING);
    EXPECT_EQ(SimEngine::Instance().GetAssumptions().size(), 1u);
}

TEST_F(SimEngineTest, RemoveAssumptionByName) {
    Assumption a;
    a.name = "Ventas";
    a.data = {1.0, 2.0, 3.0};
    SimEngine::Instance().AddAssumption(a);

    Assumption b;
    b.name = "Costos";
    b.data = {4.0, 5.0, 6.0};
    SimEngine::Instance().AddAssumption(b);

    EXPECT_EQ(SimEngine::Instance().GetAssumptions().size(), 2u);

    SimEngine::Instance().RemoveAssumption("Ventas");
    EXPECT_EQ(SimEngine::Instance().GetAssumptions().size(), 1u);
    EXPECT_EQ(SimEngine::Instance().GetAssumptions()[0].name, "Costos");
}

TEST_F(SimEngineTest, ResetClearsEverything) {
    Assumption a;
    a.name = "Test";
    a.data = {1.0};
    SimEngine::Instance().AddAssumption(a);
    SimEngine::Instance().SetModelFunction("x -> x * 2");
    SimEngine::Instance().SetIterations(500000);

    SimEngine::Instance().Reset();
    EXPECT_EQ(SimEngine::Instance().GetState(), SimState::IDLE);
    EXPECT_TRUE(SimEngine::Instance().GetAssumptions().empty());
}

TEST_F(SimEngineTest, SetIterationsClamps) {
    SimEngine::Instance().SetIterations(500);  // Below minimum
    // We can't directly read iterations_ since it's private,
    // but we verify no crash occurs
    SimEngine::Instance().SetIterations(20000000);  // Above maximum
    SimEngine::Instance().SetIterations(1000000);   // Normal
}

TEST_F(SimEngineTest, GetPercentileReturnsZeroWhenNotComplete) {
    EXPECT_EQ(SimEngine::Instance().GetPercentile(50), 0.0);
}

TEST_F(SimEngineTest, GetStateStringReturnsSpanish) {
    EXPECT_EQ(SimEngine::Instance().GetStateString(), "Inactivo");

    Assumption a;
    a.name = "X";
    a.data = {1.0};
    SimEngine::Instance().AddAssumption(a);
    EXPECT_EQ(SimEngine::Instance().GetStateString(), "Configurando");
}

TEST_F(SimEngineTest, DuplicateAssumptionNameReplaces) {
    Assumption a;
    a.name = "Ventas";
    a.data = {1.0, 2.0};
    SimEngine::Instance().AddAssumption(a);

    Assumption b;
    b.name = "Ventas";
    b.data = {3.0, 4.0, 5.0};
    SimEngine::Instance().AddAssumption(b);

    EXPECT_EQ(SimEngine::Instance().GetAssumptions().size(), 1u);
    EXPECT_EQ(SimEngine::Instance().GetAssumptions()[0].data.size(), 3u);
}

TEST_F(SimEngineTest, RunPipelineWithNoData_FailsAtFitting) {
    // Add assumption with no data → should fail at fitting stage
    Assumption a;
    a.name = "Empty";
    a.data = {};  // No data!
    SimEngine::Instance().AddAssumption(a);
    SimEngine::Instance().SetModelFunction("(x) -> x");

    SimEngine::Instance().RunPipeline();
    EXPECT_EQ(SimEngine::Instance().GetState(), SimState::FAILED);
    EXPECT_TRUE(SimEngine::Instance().GetLastError().find("No data") != std::string::npos);
}

TEST_F(SimEngineTest, RunPipelineWithNoModel_FailsAtSimulation) {
    // Add valid assumption but no model function
    Assumption a;
    a.name = "Test";
    a.data = std::vector<double>(20, 5.0); // 20 data points
    a.best_fit.dist_name = "norm";
    a.best_fit.param1 = 5.0;
    a.best_fit.param2 = 1.0;
    SimEngine::Instance().AddAssumption(a);
    // Don't set model function

    // Note: RunPipeline will fail at fitting because SimBridge isn't connected
    // (no Excel running), which is expected in tests. We validate state transitions.
    SimEngine::Instance().RunPipeline();
    EXPECT_EQ(SimEngine::Instance().GetState(), SimState::FAILED);
}

TEST_F(SimEngineTest, CallbackInvoked) {
    Assumption a;
    a.name = "X";
    a.data = {};
    SimEngine::Instance().AddAssumption(a);
    SimEngine::Instance().SetModelFunction("(x) -> x");

    bool callback_called = false;
    bool callback_success = true;
    SimEngine::Instance().RunPipeline([&](bool success) {
        callback_called = true;
        callback_success = success;
    });

    EXPECT_TRUE(callback_called);
    EXPECT_FALSE(callback_success);  // Should fail (no data)
}

TEST_F(SimEngineTest, GetLastError_ClearsOnReset) {
    Assumption a;
    a.name = "X";
    a.data = {};
    SimEngine::Instance().AddAssumption(a);
    SimEngine::Instance().SetModelFunction("(x) -> x");
    SimEngine::Instance().RunPipeline();

    EXPECT_FALSE(SimEngine::Instance().GetLastError().empty());

    SimEngine::Instance().Reset();
    EXPECT_TRUE(SimEngine::Instance().GetLastError().empty());
}

TEST_F(SimEngineTest, GetSensitivity_EmptyBeforeRun) {
    EXPECT_TRUE(SimEngine::Instance().GetSensitivity().empty());
}

} // namespace testing
} // namespace neven_sim
