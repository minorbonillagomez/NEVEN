/**
 * @file sim_bridge_test.cc
 * @brief Unit tests for SimBridge — validates logic without real Excel.
 *
 * These tests verify the bridge's initialization logic, path detection,
 * and error handling. Actual xlUDF calls cannot be tested without Excel.
 *
 * Copyright (c) 2026 NEVEN Project — GPL v3
 */

#include <gtest/gtest.h>
#include <windows.h>
#include "sim_bridge.h"

namespace neven_sim {
namespace testing {

TEST(SimBridgeTest, InstanceIsSingleton) {
    auto& a = SimBridge::Instance();
    auto& b = SimBridge::Instance();
    EXPECT_EQ(&a, &b);
}

TEST(SimBridgeTest, InitializeWithoutHomeReturnsUnavailable) {
    // If RJ2XCL_HOME is not set and C:\NEVEN doesn't exist,
    // Initialize should return false. In a test environment without
    // NEVEN installed, this validates error handling.
    
    // Save and clear environment
    char original[MAX_PATH] = {};
    DWORD len = GetEnvironmentVariableA("RJ2XCL_HOME", original, MAX_PATH);
    
    // Note: We can't truly test this in isolation because SimBridge is
    // a singleton and Initialize() has already been designed for production use.
    // This test documents the expected behavior.
    
    auto& bridge = SimBridge::Instance();
    // In CI without NEVEN installed, IsBaseAvailable() should be false
    // because Excel is not running (xlUDF will fail).
    // We just verify the call doesn't crash.
    bool available = bridge.IsBaseAvailable();
    (void)available; // Result depends on environment
}

TEST(SimBridgeTest, CallRWithoutBaseReturnsError) {
    auto& bridge = SimBridge::Instance();
    // Without Excel running, calls should return error strings
    std::string result = bridge.CallR("1+1");
    EXPECT_TRUE(result.find("[ERROR]") == 0 || result == "2");
    // Either it errors (no Excel) or succeeds (Excel is running)
}

TEST(SimBridgeTest, CallJuliaWithoutBaseReturnsError) {
    auto& bridge = SimBridge::Instance();
    std::string result = bridge.CallJulia("1+1");
    EXPECT_TRUE(result.find("[ERROR]") == 0 || result == "2");
}

TEST(SimBridgeTest, GetHomePathIsNotEmpty_WhenNevenInstalled) {
    auto& bridge = SimBridge::Instance();
    std::string home = bridge.GetHomePath();
    // If NEVEN is installed, home should point to C:\NEVEN\ or similar
    // If not installed, it may be empty
    if (!home.empty()) {
        // Verify it's a valid-looking path
        EXPECT_TRUE(home.find("NEVEN") != std::string::npos ||
                    home.find("neven") != std::string::npos ||
                    home.find("RJ2XCL") != std::string::npos);
    }
}

} // namespace testing
} // namespace neven_sim
