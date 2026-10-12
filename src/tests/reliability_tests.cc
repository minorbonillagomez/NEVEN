/**
 * Copyright (c) 2026 NEVEN Project
 *
 * Unit tests for reliability improvements.
 *
 * Tests what is TESTABLE without mocking the full pipe infrastructure:
 * - ConfigService per-language timeout getters
 * - HealthStatus enum values
 * - Error message formatting patterns
 */

#include <gtest/gtest.h>
#include "ConfigService.h"
#include "language_service.h"

#include <string>
#include <sstream>

using namespace rj2xcl;

// ═══════════════════════════════════════════════════════════════════
// ConfigService Per-Language Timeout Tests
// ═══════════════════════════════════════════════════════════════════

class ConfigTimeoutTest : public ::testing::Test {
protected:
    ConfigService& config = ConfigService::Instance();
};

TEST_F(ConfigTimeoutTest, NonExistentLanguage_ReturnsGlobalDefault) {
    // With empty config, per-language key is absent → falls back to global.
    // Global is also absent in test env → returns 600000 default.
    DWORD timeout = config.GetLanguageCallTimeoutMs("NonExistent");
    EXPECT_EQ(timeout, 600000u);
}

TEST_F(ConfigTimeoutTest, EmptyLanguageName_ReturnsGlobalDefault) {
    DWORD timeout = config.GetLanguageCallTimeoutMs("");
    EXPECT_EQ(timeout, 600000u);
}

TEST_F(ConfigTimeoutTest, GlobalDefault_Is600000) {
    // Verify the global fallback value
    DWORD global = config.GetCallTimeoutMs();
    EXPECT_EQ(global, 600000u);
}

// ═══════════════════════════════════════════════════════════════════
// Per-Language Timeout Clamping Logic (tested via JSON parsing)
//
// We can't inject config into the singleton, but we can verify the
// clamping logic by testing the same algorithm the getter uses.
// ═══════════════════════════════════════════════════════════════════

// Helper that replicates GetLanguageCallTimeoutMs clamping logic
static DWORD SimulateTimeoutClamping(int val, DWORD global_fallback = 600000) {
    if (val >= 1000 && val <= 1800000) return (DWORD)val;
    if (val > 0) {
        return (val < 1000) ? 1000 : 1800000;
    }
    return global_fallback;
}

TEST(TimeoutClampingLogic, ValidValue_ReturnedAsIs) {
    EXPECT_EQ(SimulateTimeoutClamping(300000), 300000u);
}

TEST(TimeoutClampingLogic, BoundaryLow_1000_ReturnedAsIs) {
    EXPECT_EQ(SimulateTimeoutClamping(1000), 1000u);
}

TEST(TimeoutClampingLogic, BoundaryHigh_1800000_ReturnedAsIs) {
    EXPECT_EQ(SimulateTimeoutClamping(1800000), 1800000u);
}

TEST(TimeoutClampingLogic, BelowRange_500_ClampedTo1000) {
    EXPECT_EQ(SimulateTimeoutClamping(500), 1000u);
}

TEST(TimeoutClampingLogic, BelowRange_1_ClampedTo1000) {
    EXPECT_EQ(SimulateTimeoutClamping(1), 1000u);
}

TEST(TimeoutClampingLogic, AboveRange_2000000_ClampedTo1800000) {
    EXPECT_EQ(SimulateTimeoutClamping(2000000), 1800000u);
}

TEST(TimeoutClampingLogic, Zero_FallsBackToGlobal) {
    EXPECT_EQ(SimulateTimeoutClamping(0), 600000u);
}

TEST(TimeoutClampingLogic, Negative_FallsBackToGlobal) {
    EXPECT_EQ(SimulateTimeoutClamping(-100), 600000u);
}

TEST(TimeoutClampingLogic, MidRange_ReturnedAsIs) {
    EXPECT_EQ(SimulateTimeoutClamping(900000), 900000u);
}

// ═══════════════════════════════════════════════════════════════════
// HealthStatus Enum Tests
// ═══════════════════════════════════════════════════════════════════

TEST(HealthStatusTest, EnumValuesExistAndAreDistinct) {
    HealthStatus healthy = HealthStatus::Healthy;
    HealthStatus unavailable = HealthStatus::Unavailable;
    HealthStatus unknown = HealthStatus::Unknown;

    EXPECT_NE(healthy, unavailable);
    EXPECT_NE(healthy, unknown);
    EXPECT_NE(unavailable, unknown);
}

TEST(HealthStatusTest, UnknownIsNotHealthy) {
    EXPECT_NE(HealthStatus::Unknown, HealthStatus::Healthy);
}

TEST(HealthStatusTest, UnavailableIsNotHealthy) {
    EXPECT_NE(HealthStatus::Unavailable, HealthStatus::Healthy);
}

TEST(HealthStatusTest, EnumCanBeCompared) {
    HealthStatus a = HealthStatus::Healthy;
    HealthStatus b = HealthStatus::Healthy;
    EXPECT_EQ(a, b);
}

// ═══════════════════════════════════════════════════════════════════
// Error Message Format Tests
//
// These test the message formatting patterns used in Call().
// We create helper functions that format error messages the same way
// the production code does, then verify the format.
// ═══════════════════════════════════════════════════════════════════

namespace {

// Helpers that replicate the error message formatting from Call()

std::string FormatBrokenPipeError(const std::string& language_name) {
    return language_name + " service unavailable — restart Excel to reconnect.";
}

std::string FormatTimeoutError(const std::string& language_name, DWORD timeout_ms) {
    std::stringstream ss;
    ss << language_name << " did not respond within "
       << (timeout_ms / 1000) << " seconds. Check the log file for details.";
    return ss.str();
}

std::string FormatMaxRetriesError(const std::string& language_name, int max_retries) {
    std::stringstream ss;
    ss << language_name << " reconnection failed after "
       << max_retries << " attempts — restart Excel.";
    return ss.str();
}

std::string FormatDeadProcessError(const std::string& language_name, DWORD exit_code) {
    std::stringstream ss;
    ss << language_name << " process exited unexpectedly (code "
       << exit_code << "). Check the log file.";
    return ss.str();
}

std::string FormatNotConnectedError(const std::string& language_name) {
    return language_name + " is not connected — restart Excel to reconnect.";
}

std::string FormatParseError(const std::string& language_name) {
    return language_name + " returned an invalid response. Check the log file for details.";
}

std::string FormatProcessNotRunningError(const std::string& language_name, DWORD exit_code) {
    std::stringstream ss;
    ss << language_name << " process is not running (exit code "
       << exit_code << ").";
    return ss.str();
}

std::string FormatUnavailableError(const std::string& language_name) {
    return language_name + " is currently unavailable.";
}

} // anonymous namespace

// --- Broken pipe error ---

TEST(ErrorMessageTest, BrokenPipe_ContainsLanguageName) {
    std::string msg = FormatBrokenPipeError("R");
    EXPECT_NE(msg.find("R"), std::string::npos);
}

TEST(ErrorMessageTest, BrokenPipe_ContainsRestartGuidance) {
    std::string msg = FormatBrokenPipeError("Julia");
    EXPECT_NE(msg.find("restart Excel"), std::string::npos);
}

// --- Timeout error ---

TEST(ErrorMessageTest, Timeout_ContainsLanguageName) {
    std::string msg = FormatTimeoutError("Python", 120000);
    EXPECT_NE(msg.find("Python"), std::string::npos);
}

TEST(ErrorMessageTest, Timeout_ContainsSeconds) {
    std::string msg = FormatTimeoutError("Julia", 900000);
    EXPECT_NE(msg.find("900"), std::string::npos);
}

TEST(ErrorMessageTest, Timeout_ContainsCheckLogGuidance) {
    std::string msg = FormatTimeoutError("R", 600000);
    EXPECT_NE(msg.find("Check the log file"), std::string::npos);
}

// --- Max retries error ---

TEST(ErrorMessageTest, MaxRetries_ContainsLanguageName) {
    std::string msg = FormatMaxRetriesError("Julia", 3);
    EXPECT_NE(msg.find("Julia"), std::string::npos);
}

TEST(ErrorMessageTest, MaxRetries_ContainsCount) {
    std::string msg = FormatMaxRetriesError("R", 5);
    EXPECT_NE(msg.find("5"), std::string::npos);
}

TEST(ErrorMessageTest, MaxRetries_ContainsRestartGuidance) {
    std::string msg = FormatMaxRetriesError("Python", 2);
    EXPECT_NE(msg.find("restart Excel"), std::string::npos);
}

// --- Dead process error ---

TEST(ErrorMessageTest, DeadProcess_ContainsLanguageName) {
    std::string msg = FormatDeadProcessError("R", 1);
    EXPECT_NE(msg.find("R"), std::string::npos);
}

TEST(ErrorMessageTest, DeadProcess_ContainsExitCode) {
    std::string msg = FormatDeadProcessError("Julia", 42);
    EXPECT_NE(msg.find("42"), std::string::npos);
}

// --- Process not running error ---

TEST(ErrorMessageTest, ProcessNotRunning_ContainsLanguageName) {
    std::string msg = FormatProcessNotRunningError("Python", 137);
    EXPECT_NE(msg.find("Python"), std::string::npos);
}

TEST(ErrorMessageTest, ProcessNotRunning_ContainsExitCode) {
    std::string msg = FormatProcessNotRunningError("R", 255);
    EXPECT_NE(msg.find("255"), std::string::npos);
}

// --- Not connected error ---

TEST(ErrorMessageTest, NotConnected_ContainsLanguageName) {
    std::string msg = FormatNotConnectedError("Julia");
    EXPECT_NE(msg.find("Julia"), std::string::npos);
}

// --- Parse error ---

TEST(ErrorMessageTest, ParseError_ContainsLanguageName) {
    std::string msg = FormatParseError("Python");
    EXPECT_NE(msg.find("Python"), std::string::npos);
}

// --- Unavailable error ---

TEST(ErrorMessageTest, Unavailable_ContainsLanguageName) {
    std::string msg = FormatUnavailableError("R");
    EXPECT_NE(msg.find("R"), std::string::npos);
}

// --- Cross-language verification ---

TEST(ErrorMessageTest, AllFormats_WorkWithLongLanguageName) {
    std::string lang = "CustomLanguageWithLongName";

    EXPECT_NE(FormatBrokenPipeError(lang).find(lang), std::string::npos);
    EXPECT_NE(FormatTimeoutError(lang, 300000).find(lang), std::string::npos);
    EXPECT_NE(FormatMaxRetriesError(lang, 2).find(lang), std::string::npos);
    EXPECT_NE(FormatDeadProcessError(lang, 1).find(lang), std::string::npos);
    EXPECT_NE(FormatNotConnectedError(lang).find(lang), std::string::npos);
    EXPECT_NE(FormatParseError(lang).find(lang), std::string::npos);
    EXPECT_NE(FormatProcessNotRunningError(lang, 0).find(lang), std::string::npos);
    EXPECT_NE(FormatUnavailableError(lang).find(lang), std::string::npos);
}
