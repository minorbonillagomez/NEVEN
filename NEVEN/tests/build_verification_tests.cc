/**
 * Copyright (c) 2026 NEVEN Project
 *
 * Build verification tests for MSVC security compilation flags.
 * Validates that the root CMakeLists.txt declares /GS, /guard:cf,
 * /DYNAMICBASE, and /NXCOMPAT so all targets inherit these protections.
 *
 * Validates: Requirements 4.1, 4.2, 4.3
 */

#include <gtest/gtest.h>
#include <fstream>
#include <string>
#include <sstream>

class BuildVerificationTests : public ::testing::Test {
protected:
    void SetUp() override {
        // Read the root CMakeLists.txt content once for all tests.
        // CMAKE_SOURCE_DIR is the project root; the test binary runs from
        // the build tree, so we use a relative path that works from the
        // typical build directory layout (build/<config>/ or build/).
        // We try several candidate paths to be resilient across build configs.
        const std::string candidates[] = {
            CMAKE_SOURCE_DIR "/CMakeLists.txt",  // Defined via CMake
        };

        for (const auto& path : candidates) {
            std::ifstream file(path);
            if (file.is_open()) {
                std::ostringstream ss;
                ss << file.rdbuf();
                cmake_content_ = ss.str();
                file.close();
                return;
            }
        }

        // If CMAKE_SOURCE_DIR macro isn't available, try relative fallbacks
        const std::string fallbacks[] = {
            "../../CMakeLists.txt",
            "../../../CMakeLists.txt",
            "../CMakeLists.txt",
            "CMakeLists.txt",
        };

        for (const auto& path : fallbacks) {
            std::ifstream file(path);
            if (file.is_open()) {
                std::ostringstream ss;
                ss << file.rdbuf();
                cmake_content_ = ss.str();
                file.close();
                return;
            }
        }
    }

    /**
     * @brief Checks if the CMakeLists.txt content contains a given flag string.
     */
    bool ContainsFlag(const std::string& flag) const {
        return cmake_content_.find(flag) != std::string::npos;
    }

    std::string cmake_content_;
};

// Requirement 4.1: /GS (buffer security check / stack canaries)
TEST_F(BuildVerificationTests, CMakeListsContainsGSFlag) {
    ASSERT_FALSE(cmake_content_.empty())
        << "Could not read root CMakeLists.txt — verify CMAKE_SOURCE_DIR is set";
    EXPECT_TRUE(ContainsFlag("/GS"))
        << "Root CMakeLists.txt must declare /GS (buffer security check)";
}

// Requirement 4.2: /guard:cf (Control Flow Guard)
TEST_F(BuildVerificationTests, CMakeListsContainsGuardCFFlag) {
    ASSERT_FALSE(cmake_content_.empty())
        << "Could not read root CMakeLists.txt — verify CMAKE_SOURCE_DIR is set";
    EXPECT_TRUE(ContainsFlag("/guard:cf"))
        << "Root CMakeLists.txt must declare /guard:cf (Control Flow Guard)";
}

// Requirement 4.3: /DYNAMICBASE (ASLR)
TEST_F(BuildVerificationTests, CMakeListsContainsDynamicBaseFlag) {
    ASSERT_FALSE(cmake_content_.empty())
        << "Could not read root CMakeLists.txt — verify CMAKE_SOURCE_DIR is set";
    EXPECT_TRUE(ContainsFlag("/DYNAMICBASE"))
        << "Root CMakeLists.txt must declare /DYNAMICBASE (ASLR)";
}

// Requirement 4.3: /NXCOMPAT (DEP — Data Execution Prevention)
TEST_F(BuildVerificationTests, CMakeListsContainsNXCompatFlag) {
    ASSERT_FALSE(cmake_content_.empty())
        << "Could not read root CMakeLists.txt — verify CMAKE_SOURCE_DIR is set";
    EXPECT_TRUE(ContainsFlag("/NXCOMPAT"))
        << "Root CMakeLists.txt must declare /NXCOMPAT (DEP)";
}
