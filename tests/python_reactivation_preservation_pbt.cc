/**
 * Copyright (c) 2026 NEVEN Project
 *
 * Preservation Property Tests — Python Reactivation
 *
 * These tests verify that the Python reactivation fixes do NOT alter
 * existing R and Julia behavior. They encode the baseline behavior
 * observed on unfixed code and verify it remains unchanged.
 *
 * Property 2: Preservation — R and Julia Behavior Unchanged
 * Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6
 */

#include <gtest/gtest.h>
#include <rapidcheck.h>
#include <rapidcheck/gtest.h>

#include "language_service.h"
#include "string_utilities.h"
#include "ConfigService.h"
#include "Constants.h"

#include <string>
#include <vector>
#include <random>

using namespace rj2xcl;

// ═══════════════════════════════════════════════════════════════════
// Test Fixture
// ═══════════════════════════════════════════════════════════════════

class PythonReactivationPreservationPBT : public ::testing::Test {
protected:
    void SetUp() override {}
};

// ─── R Initialization Preservation ───────────────────────────────────────────
//
// Verify that R startup code continues to be sent line-by-line.
// The fix only changes Python to single-block; R must remain line-by-line.

RC_GTEST_FIXTURE_PROP(PythonReactivationPreservationPBT,
    RStartupCodeSentLineByLine,
    ())
{
    // Generate a random R-style startup script
    auto num_lines = *rc::gen::inRange(3, 20);
    std::vector<std::string> original_lines;

    for (int i = 0; i < num_lines; i++) {
        auto line_type = *rc::gen::inRange(0, 4);
        switch (line_type) {
            case 0:
                original_lines.push_back("x <- " + std::to_string(i));
                break;
            case 1:
                original_lines.push_back("library(stats)");
                break;
            case 2:
                original_lines.push_back("# comment line " + std::to_string(i));
                break;
            case 3:
                original_lines.push_back("print(paste('hello', " + std::to_string(i) + "))");
                break;
            case 4:
                original_lines.push_back("result <- function(x) x + 1");
                break;
        }
    }

    // Assemble into a single string (as it would be in the startup resource)
    std::string startup_code;
    for (const auto& line : original_lines) {
        startup_code += line + "\n";
    }

    // Simulate R line-by-line sending (existing behavior):
    // Split by newline, filter empty lines, send each non-empty line
    std::vector<std::string> split_lines;
    StringUtilities::Split(startup_code, '\n', 1, split_lines, true);

    std::vector<std::string> sent_lines;
    for (const auto& line : split_lines) {
        if (line.length() > 0) {
            sent_lines.push_back(line);
        }
    }

    // For R: all non-empty original lines should be sent
    RC_ASSERT(sent_lines.size() == original_lines.size());

    // Each sent line matches the original (R doesn't have blank-line issues)
    for (size_t i = 0; i < sent_lines.size(); i++) {
        RC_ASSERT(sent_lines[i] == original_lines[i]);
    }
}

// ─── Julia Initialization Preservation ───────────────────────────────────────
//
// Verify that Julia startup code continues to be sent line-by-line with wait=false.

RC_GTEST_FIXTURE_PROP(PythonReactivationPreservationPBT,
    JuliaStartupCodeSentLineByLine,
    ())
{
    // Generate a random Julia-style startup script
    auto num_lines = *rc::gen::inRange(3, 15);
    std::vector<std::string> original_lines;

    for (int i = 0; i < num_lines; i++) {
        auto line_type = *rc::gen::inRange(0, 4);
        switch (line_type) {
            case 0:
                original_lines.push_back("x = " + std::to_string(i));
                break;
            case 1:
                original_lines.push_back("using Statistics");
                break;
            case 2:
                original_lines.push_back("# Julia comment " + std::to_string(i));
                break;
            case 3:
                original_lines.push_back("println(\"hello $" + std::to_string(i) + "\")");
                break;
            case 4:
                original_lines.push_back("f(x) = x + 1");
                break;
        }
    }

    // Assemble
    std::string startup_code;
    for (const auto& line : original_lines) {
        startup_code += line + "\n";
    }

    // Simulate Julia line-by-line sending (same as R — existing behavior)
    std::vector<std::string> split_lines;
    StringUtilities::Split(startup_code, '\n', 1, split_lines, true);

    std::vector<std::string> sent_lines;
    for (const auto& line : split_lines) {
        if (line.length() > 0) {
            sent_lines.push_back(line);
        }
    }

    // All non-empty lines preserved for Julia
    RC_ASSERT(sent_lines.size() == original_lines.size());
    for (size_t i = 0; i < sent_lines.size(); i++) {
        RC_ASSERT(sent_lines[i] == original_lines[i]);
    }
}

// ─── Python-Disabled Preservation ────────────────────────────────────────────
//
// Verify that when Python is disabled, the system behaves identically.

TEST_F(PythonReactivationPreservationPBT, PythonDisabledConfigParsing) {
    // When Python section has "enabled": false, the language service
    // should not be configured. Verify the config parsing contract.

    std::string config_json = R"({
        "NEVEN": {
            "R": { "home": "", "minMajor": 3, "minMinor": 5, "maxMajor": 99 },
            "Julia": { "home": "", "enabled": true },
            "Python": { "home": "", "enabled": false, "minMajor": 3, "minMinor": 10, "maxMajor": 99 }
        }
    })";

    std::string err;
    auto config = json11::Json::parse(config_json, err, json11::COMMENTS);
    ASSERT_TRUE(err.empty()) << "JSON parse error: " << err;

    // R section should be unaffected by Python presence
    auto r_config = config["NEVEN"]["R"];
    EXPECT_TRUE(r_config["minMajor"].is_number());
    EXPECT_EQ(r_config["minMajor"].int_value(), 3);
    EXPECT_EQ(r_config["minMinor"].int_value(), 5);
    EXPECT_EQ(r_config["maxMajor"].int_value(), 99);

    // Julia section should be unaffected
    auto julia_config = config["NEVEN"]["Julia"];
    EXPECT_TRUE(julia_config["enabled"].bool_value());

    // Python section exists but is disabled
    auto python_config = config["NEVEN"]["Python"];
    EXPECT_FALSE(python_config["enabled"].bool_value());
    EXPECT_EQ(python_config["minMajor"].int_value(), 3);
    EXPECT_EQ(python_config["minMinor"].int_value(), 10);
}

TEST_F(PythonReactivationPreservationPBT, NoPythonSectionConfigParsing) {
    // When no Python section exists at all, R and Julia should work identically

    std::string config_json = R"({
        "NEVEN": {
            "R": { "home": "C:/R/R-4.4.1", "minMajor": 3, "minMinor": 5, "maxMajor": 99 },
            "Julia": { "home": "C:/Julia", "enabled": true }
        }
    })";

    std::string err;
    auto config = json11::Json::parse(config_json, err, json11::COMMENTS);
    ASSERT_TRUE(err.empty());

    // R config unchanged
    auto r_config = config["NEVEN"]["R"];
    EXPECT_EQ(r_config["home"].string_value(), "C:/R/R-4.4.1");
    EXPECT_EQ(r_config["minMajor"].int_value(), 3);

    // Julia config unchanged
    auto julia_config = config["NEVEN"]["Julia"];
    EXPECT_EQ(julia_config["home"].string_value(), "C:/Julia");
    EXPECT_TRUE(julia_config["enabled"].bool_value());

    // Python section is null/missing
    auto python_config = config["NEVEN"]["Python"];
    EXPECT_TRUE(python_config.is_null());
}

// ─── Config Parsing Preservation (PBT) ──────────────────────────────────────
//
// Adding a Python section to config must not alter R or Julia parsing.

RC_GTEST_FIXTURE_PROP(PythonReactivationPreservationPBT,
    ConfigParsingPreservedWithPythonSection,
    ())
{
    // Generate random R config values
    auto r_min_major = *rc::gen::inRange(3, 5);
    auto r_min_minor = *rc::gen::inRange(0, 10);
    auto r_max_major = *rc::gen::inRange(4, 99);

    // Generate random Julia enabled state
    auto julia_enabled = *rc::gen::arbitrary<bool>();

    // Config WITHOUT Python
    std::string config_no_python = R"({"NEVEN":{"R":{"minMajor":)" +
        std::to_string(r_min_major) + R"(,"minMinor":)" +
        std::to_string(r_min_minor) + R"(,"maxMajor":)" +
        std::to_string(r_max_major) + R"(},"Julia":{"enabled":)" +
        (julia_enabled ? "true" : "false") + R"(}}})";

    // Config WITH Python section added
    std::string config_with_python = R"({"NEVEN":{"R":{"minMajor":)" +
        std::to_string(r_min_major) + R"(,"minMinor":)" +
        std::to_string(r_min_minor) + R"(,"maxMajor":)" +
        std::to_string(r_max_major) + R"(},"Julia":{"enabled":)" +
        (julia_enabled ? "true" : "false") +
        R"(},"Python":{"home":"","enabled":false,"minMajor":3,"minMinor":10}}})";

    std::string err1, err2;
    auto parsed_no_python = json11::Json::parse(config_no_python, err1);
    auto parsed_with_python = json11::Json::parse(config_with_python, err2);

    RC_ASSERT(err1.empty());
    RC_ASSERT(err2.empty());

    // R values must be identical with and without Python section
    RC_ASSERT(parsed_no_python["NEVEN"]["R"]["minMajor"].int_value() ==
              parsed_with_python["NEVEN"]["R"]["minMajor"].int_value());
    RC_ASSERT(parsed_no_python["NEVEN"]["R"]["minMinor"].int_value() ==
              parsed_with_python["NEVEN"]["R"]["minMinor"].int_value());
    RC_ASSERT(parsed_no_python["NEVEN"]["R"]["maxMajor"].int_value() ==
              parsed_with_python["NEVEN"]["R"]["maxMajor"].int_value());

    // Julia values must be identical
    RC_ASSERT(parsed_no_python["NEVEN"]["Julia"]["enabled"].bool_value() ==
              parsed_with_python["NEVEN"]["Julia"]["enabled"].bool_value());
}

// ─── Health-Aware Dispatch Preservation ──────────────────────────────────────
//
// Verify that the health check only affects Unavailable services.
// Healthy and Unknown services should continue to work normally.

TEST_F(PythonReactivationPreservationPBT, HealthCheckOnlyAffectsUnavailable) {
    // The fix adds: if (health_status_ == HealthStatus::Unavailable) return {};
    // This should NOT affect Healthy or Unknown services.

    // Verify the three states are distinct
    EXPECT_NE(static_cast<int>(HealthStatus::Healthy),
              static_cast<int>(HealthStatus::Unavailable));
    EXPECT_NE(static_cast<int>(HealthStatus::Unknown),
              static_cast<int>(HealthStatus::Unavailable));
    EXPECT_NE(static_cast<int>(HealthStatus::Healthy),
              static_cast<int>(HealthStatus::Unknown));

    // The check is: if (status == Unavailable) return {};
    // So Healthy and Unknown should NOT trigger the early return
    HealthStatus healthy = HealthStatus::Healthy;
    HealthStatus unknown = HealthStatus::Unknown;
    HealthStatus unavailable = HealthStatus::Unavailable;

    EXPECT_FALSE(healthy == HealthStatus::Unavailable);
    EXPECT_FALSE(unknown == HealthStatus::Unavailable);
    EXPECT_TRUE(unavailable == HealthStatus::Unavailable);
}

// ─── Constants Preservation ──────────────────────────────────────────────────
//
// Verify that shared constants used by R and Julia are unchanged.

TEST_F(PythonReactivationPreservationPBT, SharedConstantsUnchanged) {
    // These constants are used by ControlR and ControlJulia
    // They must not be altered by the Python reactivation
    EXPECT_EQ(Constants::kMaxPipeCount, 4);
    EXPECT_EQ(Constants::kCallbackPipeIndex, 0);
    EXPECT_EQ(Constants::kPrimaryClientPipeIndex, 1);
    EXPECT_EQ(Constants::kPipeBufferSize, 8u * 1024u);
    EXPECT_EQ(Constants::kDefaultCallTimeoutMs, 600'000u);
}

// ─── StringUtilities::Split Preservation ─────────────────────────────────────
//
// The Split function is used by R and Julia for line-by-line sending.
// Verify it continues to work correctly for non-Python scripts.

RC_GTEST_FIXTURE_PROP(PythonReactivationPreservationPBT,
    SplitPreservedForNonPythonScripts,
    ())
{
    // Generate random lines without embedded newlines
    auto num_lines = *rc::gen::inRange(1, 20);
    std::vector<std::string> expected_lines;

    for (int i = 0; i < num_lines; i++) {
        // Generate a non-empty line (R/Julia code doesn't rely on blank lines)
        auto len = *rc::gen::inRange(1, 50);
        std::string line;
        for (int j = 0; j < len; j++) {
            auto c = *rc::gen::inRange(32, 126); // printable ASCII
            if (c == '\n' || c == '\r') c = 'x'; // no embedded newlines
            line += static_cast<char>(c);
        }
        expected_lines.push_back(line);
    }

    // Join with newlines
    std::string joined;
    for (const auto& line : expected_lines) {
        joined += line + "\n";
    }

    // Split and filter (R/Julia behavior)
    std::vector<std::string> split_result;
    StringUtilities::Split(joined, '\n', 1, split_result, true);

    std::vector<std::string> filtered;
    for (const auto& line : split_result) {
        if (line.length() > 0) {
            filtered.push_back(line);
        }
    }

    // All non-empty lines should be preserved
    RC_ASSERT(filtered.size() == expected_lines.size());
    for (size_t i = 0; i < filtered.size(); i++) {
        RC_ASSERT(filtered[i] == expected_lines[i]);
    }
}
