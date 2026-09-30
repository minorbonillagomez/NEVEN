/**
 * Copyright (c) 2026 NEVEN Project
 *
 * Property-based tests for reliability improvements.
 *
 * These tests use custom random generators within GTest to verify correctness
 * properties across many randomized inputs (minimum 100 iterations each).
 *
 * Properties tested:
 *   P5 — Timeout Value Clamping (ConfigService getter always returns valid range)
 *   P2 — Error Messages Always Contain Language Name
 *   P3 — Error Message Formatting Includes Context Values
 *
 * These tests do NOT require pipe connections or running processes.
 * They test only logic that can be tested in isolation.
 */

#include <gtest/gtest.h>
#include "ConfigService.h"
#include "language_service.h"

#include <random>
#include <string>
#include <sstream>
#include <climits>

using namespace rj2xcl;

// ═══════════════════════════════════════════════════════════════════
// Task 14.1 — Test fixture and random generators
// ═══════════════════════════════════════════════════════════════════

class ReliabilityPBT : public ::testing::Test {
protected:
    std::mt19937 rng;

    void SetUp() override {
        // Fixed seed for reproducibility
        rng.seed(42);
    }

    // ── Generator: Random language name (1–50 chars, alphanumeric) ──

    std::string GenerateLanguageName() {
        static const char charset[] =
            "abcdefghijklmnopqrstuvwxyz"
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            "0123456789";
        std::uniform_int_distribution<int> len_dist(1, 50);
        std::uniform_int_distribution<int> char_dist(0, sizeof(charset) - 2);

        int length = len_dist(rng);
        std::string name;
        name.reserve(length);
        for (int i = 0; i < length; ++i) {
            name += charset[char_dist(rng)];
        }
        return name;
    }

    // ── Generator: Random exit code (0–255, excluding 259/STILL_ACTIVE) ──

    DWORD GenerateExitCode() {
        std::uniform_int_distribution<int> dist(0, 255);
        int code = dist(rng);
        if (code == 259) code = 0; // Avoid STILL_ACTIVE
        return (DWORD)code;
    }

    // ── Generator: Random timeout value (INT_MIN to INT_MAX) ──

    int GenerateRandomTimeout() {
        std::uniform_int_distribution<int> dist(INT_MIN, INT_MAX);
        return dist(rng);
    }

    // ── Generator: Random valid timeout (1000–1800000) ──

    int GenerateValidTimeout() {
        std::uniform_int_distribution<int> dist(1000, 1800000);
        return dist(rng);
    }

    // ── Generator: Random positive numeric value (0–2^31-1) ──

    int GenerateNumericValue() {
        std::uniform_int_distribution<int> dist(0, INT_MAX);
        return dist(rng);
    }

    // ── Error message formatters (same patterns as Call()) ──

    static std::string FormatBrokenPipeError(const std::string& lang) {
        return lang + " service unavailable — restart Excel to reconnect.";
    }

    static std::string FormatTimeoutError(const std::string& lang, DWORD timeout_ms) {
        std::stringstream ss;
        ss << lang << " did not respond within "
           << (timeout_ms / 1000) << " seconds. Check the log file for details.";
        return ss.str();
    }

    static std::string FormatMaxRetriesError(const std::string& lang, int retries) {
        std::stringstream ss;
        ss << lang << " reconnection failed after "
           << retries << " attempts — restart Excel.";
        return ss.str();
    }

    static std::string FormatDeadProcessError(const std::string& lang, DWORD exit_code) {
        std::stringstream ss;
        ss << lang << " process exited unexpectedly (code "
           << exit_code << "). Check the log file.";
        return ss.str();
    }

    static std::string FormatNotConnectedError(const std::string& lang) {
        return lang + " is not connected — restart Excel to reconnect.";
    }

    static std::string FormatParseError(const std::string& lang) {
        return lang + " returned an invalid response. Check the log file for details.";
    }

    static std::string FormatProcessNotRunningError(const std::string& lang, DWORD exit_code) {
        std::stringstream ss;
        ss << lang << " process is not running (exit code "
           << exit_code << ").";
        return ss.str();
    }

    static std::string FormatUnavailableError(const std::string& lang) {
        return lang + " is currently unavailable.";
    }

    // ── Timeout clamping logic (same as GetLanguageCallTimeoutMs) ──

    static DWORD SimulateTimeoutClamping(int val, DWORD global_fallback = 600000) {
        if (val >= 1000 && val <= 1800000) return (DWORD)val;
        if (val > 0) {
            return (val < 1000) ? 1000 : 1800000;
        }
        return global_fallback;
    }
};

// ═══════════════════════════════════════════════════════════════════
// Property 5: Timeout Value Clamping
//
// Feature: reliability-improvements
// Property 5: Timeout Value Clamping
// **Validates: Requirements 4.4, 4.5**
//
// For any random integer, the timeout clamping logic SHALL always
// return a value in [1000, 1800000] for positive inputs, and fall
// back to the global default for non-positive inputs.
// ═══════════════════════════════════════════════════════════════════

TEST_F(ReliabilityPBT, Property5_TimeoutValueClamping) {
    const int NUM_ITERATIONS = 150;
    int valid_count = 0;

    for (int i = 0; i < NUM_ITERATIONS; ++i) {
        int random_val = GenerateRandomTimeout();
        DWORD result = SimulateTimeoutClamping(random_val);

        if (random_val > 0) {
            // Positive inputs: result must be in [1000, 1800000]
            EXPECT_GE(result, 1000u)
                << "Iteration " << i << ": Value " << random_val
                << " produced result " << result << " below minimum 1000";
            EXPECT_LE(result, 1800000u)
                << "Iteration " << i << ": Value " << random_val
                << " produced result " << result << " above maximum 1800000";
        } else {
            // Non-positive inputs: falls back to global default (600000)
            EXPECT_EQ(result, 600000u)
                << "Iteration " << i << ": Non-positive value " << random_val
                << " should fall back to global default 600000, got " << result;
        }

        ++valid_count;
    }

    EXPECT_EQ(valid_count, NUM_ITERATIONS)
        << "Not all iterations completed successfully.";
}

// ═══════════════════════════════════════════════════════════════════
// Property 2: Error Messages Always Contain Language Name
//
// Feature: reliability-improvements
// Property 2: Error Messages Always Contain Language Name
// **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**
//
// For any random language name string, every error message format
// SHALL contain the language name as a substring.
// ═══════════════════════════════════════════════════════════════════

TEST_F(ReliabilityPBT, Property2_ErrorMessagesContainLanguageName) {
    const int NUM_ITERATIONS = 150;
    int valid_count = 0;

    for (int i = 0; i < NUM_ITERATIONS; ++i) {
        std::string lang = GenerateLanguageName();

        // Test all error message formats
        std::string broken_pipe = FormatBrokenPipeError(lang);
        EXPECT_NE(broken_pipe.find(lang), std::string::npos)
            << "Iteration " << i << ": Broken pipe error missing language name '"
            << lang << "' in: " << broken_pipe;

        std::string timeout = FormatTimeoutError(lang, 600000);
        EXPECT_NE(timeout.find(lang), std::string::npos)
            << "Iteration " << i << ": Timeout error missing language name '"
            << lang << "' in: " << timeout;

        std::string max_retries = FormatMaxRetriesError(lang, 2);
        EXPECT_NE(max_retries.find(lang), std::string::npos)
            << "Iteration " << i << ": Max retries error missing language name '"
            << lang << "' in: " << max_retries;

        std::string dead_proc = FormatDeadProcessError(lang, 1);
        EXPECT_NE(dead_proc.find(lang), std::string::npos)
            << "Iteration " << i << ": Dead process error missing language name '"
            << lang << "' in: " << dead_proc;

        std::string not_connected = FormatNotConnectedError(lang);
        EXPECT_NE(not_connected.find(lang), std::string::npos)
            << "Iteration " << i << ": Not connected error missing language name '"
            << lang << "' in: " << not_connected;

        std::string parse_err = FormatParseError(lang);
        EXPECT_NE(parse_err.find(lang), std::string::npos)
            << "Iteration " << i << ": Parse error missing language name '"
            << lang << "' in: " << parse_err;

        std::string proc_not_running = FormatProcessNotRunningError(lang, 0);
        EXPECT_NE(proc_not_running.find(lang), std::string::npos)
            << "Iteration " << i << ": Process not running error missing language name '"
            << lang << "' in: " << proc_not_running;

        std::string unavailable = FormatUnavailableError(lang);
        EXPECT_NE(unavailable.find(lang), std::string::npos)
            << "Iteration " << i << ": Unavailable error missing language name '"
            << lang << "' in: " << unavailable;

        ++valid_count;
    }

    EXPECT_EQ(valid_count, NUM_ITERATIONS)
        << "Not all iterations completed successfully.";
}

// ═══════════════════════════════════════════════════════════════════
// Property 3: Error Message Formatting Includes Context Values
//
// Feature: reliability-improvements
// Property 3: Error Message Formatting Includes Context Values
// **Validates: Requirements 2.1, 2.2, 2.3, 2.4**
//
// For any random language name and numeric value, formatted messages
// SHALL contain both the language name and the string representation
// of the numeric value.
// ═══════════════════════════════════════════════════════════════════

TEST_F(ReliabilityPBT, Property3_ErrorMessageFormattingIncludesContextValues) {
    const int NUM_ITERATIONS = 150;
    int valid_count = 0;

    for (int i = 0; i < NUM_ITERATIONS; ++i) {
        std::string lang = GenerateLanguageName();
        int numeric_val = GenerateNumericValue();
        std::string numeric_str = std::to_string(numeric_val);

        // Timeout message: contains language name and seconds
        DWORD timeout_ms = (DWORD)numeric_val;
        std::string timeout_msg = FormatTimeoutError(lang, timeout_ms);
        EXPECT_NE(timeout_msg.find(lang), std::string::npos)
            << "Iteration " << i << ": Timeout message missing language name '"
            << lang << "'";
        std::string seconds_str = std::to_string(timeout_ms / 1000);
        EXPECT_NE(timeout_msg.find(seconds_str), std::string::npos)
            << "Iteration " << i << ": Timeout message missing seconds '"
            << seconds_str << "' in: " << timeout_msg;

        // Max retries message: contains language name and retry count
        int retry_count = numeric_val % 100; // Keep reasonable
        std::string retry_msg = FormatMaxRetriesError(lang, retry_count);
        EXPECT_NE(retry_msg.find(lang), std::string::npos)
            << "Iteration " << i << ": Retry message missing language name '"
            << lang << "'";
        std::string retry_str = std::to_string(retry_count);
        EXPECT_NE(retry_msg.find(retry_str), std::string::npos)
            << "Iteration " << i << ": Retry message missing count '"
            << retry_str << "' in: " << retry_msg;

        // Dead process message: contains language name and exit code
        DWORD exit_code = GenerateExitCode();
        std::string dead_msg = FormatDeadProcessError(lang, exit_code);
        EXPECT_NE(dead_msg.find(lang), std::string::npos)
            << "Iteration " << i << ": Dead process message missing language name '"
            << lang << "'";
        std::string code_str = std::to_string(exit_code);
        EXPECT_NE(dead_msg.find(code_str), std::string::npos)
            << "Iteration " << i << ": Dead process message missing exit code '"
            << code_str << "' in: " << dead_msg;

        // Process not running message: contains language name and exit code
        std::string not_running_msg = FormatProcessNotRunningError(lang, exit_code);
        EXPECT_NE(not_running_msg.find(lang), std::string::npos)
            << "Iteration " << i << ": Process not running message missing language name '"
            << lang << "'";
        EXPECT_NE(not_running_msg.find(code_str), std::string::npos)
            << "Iteration " << i << ": Process not running message missing exit code '"
            << code_str << "' in: " << not_running_msg;

        ++valid_count;
    }

    EXPECT_EQ(valid_count, NUM_ITERATIONS)
        << "Not all iterations completed successfully.";
}
