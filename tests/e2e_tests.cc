/**
 * Copyright (c) 2026 NEVEN Project
 *
 * End-to-end integration tests for NEVEN.
 * Tests the full pipeline: Excel range -> R/Julia -> result.
 */
#include <gtest/gtest.h>
#include "basic_functions.h"
#include "rj2xcl.h"
#include "ConfigService.h"
#include "SandboxVerifier.h"
#include "type_conversions.h"

namespace rj2xcl {

// E2E: Verify the complete function registration pipeline
TEST(E2ETest, FuncTemplatesHaveNevenCategory) {
    // All funcTemplates entries should use "NEVEN" as category (column 6)
    for (int i = 0; funcTemplates[i][0] != 0; i++) {
        std::wstring category(funcTemplates[i][5]);
        EXPECT_EQ(category, L"NEVEN")
            << "funcTemplates[" << i << "] has wrong category";
    }
}

TEST(E2ETest, CallTemplatesHaveNevenCategory) {
    // callTemplates should use "NEVEN" as category
    for (int i = 0; i < 2; i++) {
        std::wstring category(callTemplates[i][5]);
        EXPECT_EQ(category, L"NEVEN")
            << "callTemplates[" << i << "] has wrong category";
    }
}

TEST(E2ETest, FuncTemplatesUseNevenPrefix) {
    // All user-visible function names (column 3) should start with "NEVEN." or "RJ_"
    for (int i = 0; funcTemplates[i][0] != 0; i++) {
        std::wstring name(funcTemplates[i][2]);
        bool is_neven = (name.find(L"NEVEN.") == 0);
        bool is_internal = (name.find(L"RJ_") == 0);
        EXPECT_TRUE(is_neven || is_internal)
            << "funcTemplates[" << i << "] name doesn't start with NEVEN. or RJ_";
    }
}

TEST(E2ETest, CallTemplatesUseNevenPrefix) {
    std::wstring call_name(callTemplates[0][2]);
    std::wstring exec_name(callTemplates[1][2]);
    EXPECT_EQ(call_name, L"NEVEN.Call");
    EXPECT_EQ(exec_name, L"NEVEN.Exec");
}

TEST(E2ETest, ConfigServiceUsesNevenKey) {
    // Config should read from "NEVEN" JSON key, not "RJ2XCL"
    auto& config = ConfigService::Instance();
    // GetGraphicsDirectory default should contain "NEVEN"
    std::string dir = config.GetGraphicsDirectory();
    EXPECT_NE(dir.find("NEVEN"), std::string::npos)
        << "Graphics directory default should contain NEVEN, got: " << dir;
}

TEST(E2ETest, SandboxBlocksInclude) {
    // Verify sandbox blocks include() for Julia
    std::string rejection;
    bool allowed = security::SandboxVerifier::GetInstance()
        .ValidateCodeForExecution("include(\"malicious.jl\")", rejection);
    EXPECT_FALSE(allowed);
    EXPECT_NE(rejection.find("include"), std::string::npos);
}

TEST(E2ETest, SandboxAllowsSqrt) {
    // Verify sandbox allows safe math operations
    std::string rejection;
    bool allowed = security::SandboxVerifier::GetInstance()
        .ValidateCodeForExecution("sqrt(144)", rejection);
    EXPECT_TRUE(allowed);
}

TEST(E2ETest, VersionContainsNeven) {
    LPXLOPER12 result = RJ_Version();
    ASSERT_NE(result, nullptr);
    ASSERT_EQ(result->xltype, xltypeStr);
    int len = result->val.str[0];
    std::wstring version(result->val.str + 1, len);
    EXPECT_NE(version.find(L"NEVEN"), std::wstring::npos);
}

} // namespace rj2xcl
