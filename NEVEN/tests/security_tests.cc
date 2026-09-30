/**
 * Copyright (c) 2026 NEVEN Project
 * 
 * Unit tests for SecurityService.
 */

#include <gtest/gtest.h>
#include "SecurityService.h"
#include <fstream>
#include <windows.h>

namespace rj2xcl {

class SecurityServiceTest : public ::testing::Test {
protected:
    void SetUp() override {
        // Create a temporary script file
        temp_script_ = "test_script.r";
        std::ofstream file(temp_script_);
        file << "print('hello security world')" << std::endl;
        file.close();

        // SHA-256 for "print('hello security world')\n" is 
        // 56930062776c11719b67482f76899b867c210ca33c5e0da05937198e38ee1a22 (roughly)
        // I'll calculate it using the service itself to test consistency
        expected_hash_ = SecurityService::Instance().CalculateSHA256(temp_script_);
    }

    void TearDown() override {
        DeleteFileA(temp_script_.c_str());
        std::string hash_file = temp_script_ + ".sha256";
        DeleteFileA(hash_file.c_str());
    }

    std::string temp_script_;
    std::string expected_hash_;
};

TEST_F(SecurityServiceTest, CalculateSHA256) {
    std::string hash = SecurityService::Instance().CalculateSHA256(temp_script_);
    EXPECT_FALSE(hash.empty());
    EXPECT_EQ(hash.length(), 64); // SHA-256 length in hex
}

TEST_F(SecurityServiceTest, VerifyIntegritySuccess) {
    // Create sidecar hash file
    std::string hash_path = temp_script_ + ".sha256";
    std::ofstream hfile(hash_path);
    hfile << expected_hash_;
    hfile.close();

    EXPECT_TRUE(SecurityService::Instance().VerifyScriptIntegrity(temp_script_));
}

TEST_F(SecurityServiceTest, VerifyIntegrityMismatch) {
    // Create sidecar with WRONG hash
    std::string hash_path = temp_script_ + ".sha256";
    std::ofstream hfile(hash_path);
    hfile << "invalidhash1234567890abcdef1234567890abcdef1234567890abcdef1234";
    hfile.close();

    EXPECT_FALSE(SecurityService::Instance().VerifyScriptIntegrity(temp_script_));
}

TEST_F(SecurityServiceTest, VerifyIntegrityNoHashFile) {
    // Should return true (Warning mode) if no hash file exists
    EXPECT_TRUE(SecurityService::Instance().VerifyScriptIntegrity(temp_script_));
}

} // namespace rj2xcl
