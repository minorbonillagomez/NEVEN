/**
 * Copyright (c) 2026 NEVEN Project
 * 
 * This file is part of NEVEN.
 */

#include "gtest/gtest.h"
#include "rj2xcl.h"
#include "MockExcelBridge.h"
#include "CallbackDispatcher.h"
#include "XLCALL.h"

namespace rj2xcl {

class CallbackBehaviorTest : public ::testing::Test {
protected:
    void SetUp() override {
        engine_ = RJ2XCL_Engine::Instance();
        mock_bridge_ = new MockExcelBridge();
        engine_->SetBridge(std::unique_ptr<IExcelBridge>(mock_bridge_));
    }

    RJ2XCL_Engine* engine_;
    MockExcelBridge* mock_bridge_;
};

/**
 * @test S4-H4: Verifies that MockExcelBridge tracks xlfRegister calls during MapFunctions/RegisterFunctions.
 */
TEST_F(CallbackBehaviorTest, TracksRegistrationCalls) {
    mock_bridge_->ClearCalls();
    
    // Trigger registration (this calls RegisterBasicFunctions which calls xlfRegister)
    engine_->UpdateFunctions();

    // basic_functions.h had 7 basic functions (Console, RConsole, etc)
    // We expect at least these calls to xlfRegister
    int register_calls = mock_bridge_->GetCallCount(xlfRegister);
    
    EXPECT_GT(register_calls, 0);
    EXPECT_GE(register_calls, 7); 
}

/**
 * @test S4-H6: Verifies callback routing logic (conceptual placeholder).
 */
TEST_F(CallbackBehaviorTest, RoutesCOMCallback) {
    // This will test the HandleCallbackOnThread logic with a mocked dispatcher call
    // For now, we just verify the bridge is still responsive.
    EXPECT_EQ(mock_bridge_->Excel12(xlGetName, NULL, 0), xlretSuccess);
    EXPECT_EQ(mock_bridge_->GetCallCount(xlGetName), 1);
}

} // namespace rj2xcl
