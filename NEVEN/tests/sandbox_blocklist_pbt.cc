/**
 * Copyright (c) 2026 NEVEN Project
 *
 * Property-based tests for SandboxVerifier blocklist enforcement.
 *
 * These tests use rapidcheck integrated with Google Test to verify that
 * the SandboxVerifier correctly blocks any code containing a blocklisted
 * pattern, regardless of surrounding code context, whitespace insertion,
 * or case variation.
 *
 * Feature: security-remediation
 * Property 4: Sandbox blocklist enforcement
 *
 * Properties tested:
 *   P4 — For any code string containing a blocked pattern (whitespace-stripped,
 *         case-normalized), ValidateFromAnySource returns false (Blocked).
 *
 * **Validates: Requirements 3.3, 3.4, 10.1, 10.2**
 */

#include <gtest/gtest.h>
#include <rapidcheck.h>
#include <rapidcheck/gtest.h>

#include "SandboxVerifier.h"

#include <algorithm>
#include <string>
#include <vector>

using rj2xcl::security::SandboxVerifier;
using rj2xcl::security::ExecutionSource;

// ═══════════════════════════════════════════════════════════════════
// Blocked pattern lists for generators
//
// These are the canonical blocked patterns that the SandboxVerifier
// must detect. The generator picks one at random and embeds it in
// surrounding random code to verify detection in any context.
// ═══════════════════════════════════════════════════════════════════

static const std::vector<std::string> kRBlockedPatterns = {
    "system(",
    "shell(",
    "file.remove(",
    "download.file(",
    "sys.getenv(",
    ".internal(",
    ".call(",
};

static const std::vector<std::string> kJuliaBlockedPatterns = {
    "run(",
    "ccall(",
    "unsafe_load(",
    "unsafe_wrap(",
    "env[",
};

// ═══════════════════════════════════════════════════════════════════
// Helper: Generate random "safe" code characters that won't
// accidentally form a blocked pattern on their own.
// Uses digits and simple arithmetic operators.
// ═══════════════════════════════════════════════════════════════════

static rc::Gen<std::string> genSafeCodeFragment() {
    return rc::gen::exec([]() {
        int len = *rc::gen::inRange(0, 50);
        std::string result;
        result.reserve(static_cast<size_t>(len));
        for (int i = 0; i < len; ++i) {
            // Use digits and simple arithmetic operators that won't form blocked patterns
            char c = *rc::gen::element(
                '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
                ' ', '+', '-', '*', ',', '\n', '\t');
            result += c;
        }
        return result;
    });
}

// ═══════════════════════════════════════════════════════════════════
// Helper: Insert random whitespace characters into a pattern.
// The SandboxVerifier strips whitespace before matching, so the
// pattern should still be detected.
// ═══════════════════════════════════════════════════════════════════

static rc::Gen<std::string> genWhitespaceInserted(const std::string& pattern) {
    return rc::gen::exec([pattern]() {
        std::string result;
        for (char c : pattern) {
            // Randomly insert 0-2 whitespace chars before each character
            int ws_count = *rc::gen::inRange(0, 3);
            for (int i = 0; i < ws_count; ++i) {
                char ws = *rc::gen::element(' ', '\t', '\n', '\r');
                result += ws;
            }
            result += c;
        }
        return result;
    });
}

// ═══════════════════════════════════════════════════════════════════
// Helper: Randomize case of a pattern.
// The SandboxVerifier normalizes to lowercase, so mixed-case
// variants should still be detected.
// ═══════════════════════════════════════════════════════════════════

static rc::Gen<std::string> genCaseRandomized(const std::string& pattern) {
    return rc::gen::exec([pattern]() {
        std::string result = pattern;
        for (char& c : result) {
            if (std::isalpha(static_cast<unsigned char>(c))) {
                bool upper = *rc::gen::arbitrary<bool>();
                c = upper ? std::toupper(static_cast<unsigned char>(c))
                          : std::tolower(static_cast<unsigned char>(c));
            }
        }
        return result;
    });
}

// ═══════════════════════════════════════════════════════════════════
// Property 4: Sandbox blocklist enforcement
//
// Feature: security-remediation
// Property 4: Sandbox blocklist enforcement
// **Validates: Requirements 3.3, 3.4, 10.1, 10.2**
//
// For any code string containing a function pattern from the R or
// Julia blocklist (including whitespace-stripped and case-normalized
// variants), the SandboxVerifier SHALL return false (Blocked)
// regardless of surrounding code context.
// ═══════════════════════════════════════════════════════════════════

RC_GTEST_PROP(SandboxBlocklistPBT, RBlockedPatternsAlwaysBlocked, ()) {
    // Pick a random R blocked pattern
    auto patternIdx = *rc::gen::inRange<size_t>(0, kRBlockedPatterns.size());
    const std::string& basePattern = kRBlockedPatterns[patternIdx];

    // Randomize case (verifier normalizes to lowercase)
    auto pattern = *genCaseRandomized(basePattern);

    // Generate random surrounding code
    auto prefix = *genSafeCodeFragment();
    auto suffix = *genSafeCodeFragment();

    // Embed the blocked pattern in surrounding code
    std::string code = prefix + pattern + suffix;

    auto& verifier = SandboxVerifier::GetInstance();
    std::string rejection_reason;

    bool result = verifier.ValidateFromAnySource(
        code, ExecutionSource::ExcelCell, rejection_reason);

    // Assert: code containing a blocked pattern must be rejected
    RC_ASSERT(!result);
    RC_ASSERT(!rejection_reason.empty());
}

RC_GTEST_PROP(SandboxBlocklistPBT, JuliaBlockedPatternsAlwaysBlocked, ()) {
    // Pick a random Julia blocked pattern
    auto patternIdx = *rc::gen::inRange<size_t>(0, kJuliaBlockedPatterns.size());
    const std::string& basePattern = kJuliaBlockedPatterns[patternIdx];

    // Randomize case (verifier normalizes to lowercase)
    auto pattern = *genCaseRandomized(basePattern);

    // Generate random surrounding code
    auto prefix = *genSafeCodeFragment();
    auto suffix = *genSafeCodeFragment();

    // Embed the blocked pattern in surrounding code
    std::string code = prefix + pattern + suffix;

    auto& verifier = SandboxVerifier::GetInstance();
    std::string rejection_reason;

    bool result = verifier.ValidateFromAnySource(
        code, ExecutionSource::ExcelCell, rejection_reason);

    // Assert: code containing a blocked pattern must be rejected
    RC_ASSERT(!result);
    RC_ASSERT(!rejection_reason.empty());
}

RC_GTEST_PROP(SandboxBlocklistPBT, WhitespaceBypassAttemptStillBlocked, ()) {
    // Combine R and Julia patterns for this test
    std::vector<std::string> allPatterns;
    allPatterns.insert(allPatterns.end(), kRBlockedPatterns.begin(), kRBlockedPatterns.end());
    allPatterns.insert(allPatterns.end(), kJuliaBlockedPatterns.begin(), kJuliaBlockedPatterns.end());

    // Pick a random pattern
    auto patternIdx = *rc::gen::inRange<size_t>(0, allPatterns.size());
    const std::string& basePattern = allPatterns[patternIdx];

    // Insert random whitespace into the pattern (bypass attempt)
    auto wsPattern = *genWhitespaceInserted(basePattern);

    // Also randomize case
    std::string mixedCase = wsPattern;
    for (char& c : mixedCase) {
        if (std::isalpha(static_cast<unsigned char>(c))) {
            bool upper = *rc::gen::arbitrary<bool>();
            c = upper ? std::toupper(static_cast<unsigned char>(c))
                      : std::tolower(static_cast<unsigned char>(c));
        }
    }

    // Generate random surrounding code
    auto prefix = *genSafeCodeFragment();
    auto suffix = *genSafeCodeFragment();

    // Embed the whitespace-inserted pattern in surrounding code
    std::string code = prefix + mixedCase + suffix;

    auto& verifier = SandboxVerifier::GetInstance();
    std::string rejection_reason;

    bool result = verifier.ValidateFromAnySource(
        code, ExecutionSource::ExcelCell, rejection_reason);

    // Assert: whitespace-inserted patterns must still be detected
    // (verifier strips whitespace before matching)
    RC_ASSERT(!result);
    RC_ASSERT(!rejection_reason.empty());
}

// ═══════════════════════════════════════════════════════════════════
// Property 5: Sandbox error message specificity
//
// Feature: security-remediation
// Property 5: Sandbox error message specificity
// **Validates: Requirements 3.7, 10.3**
//
// For any code string that is blocked by the SandboxVerifier due to
// a known blocked pattern, the rejection_reason SHALL contain the
// name of the specific blocked function or pattern that triggered
// the rejection.
// ═══════════════════════════════════════════════════════════════════

namespace {

/**
 * @brief Mapping from blocked pattern (as it appears in code) to the
 * expected function name that must appear in the rejection_reason.
 */
struct BlockedPatternExpectation {
    std::string pattern;           ///< The blocked pattern to embed in code
    std::string expected_in_reason; ///< Substring that must appear in rejection_reason
};

static const std::vector<BlockedPatternExpectation> kPatternExpectations = {
    {"system(",        "system"},
    {"shell(",         "shell"},
    {"download.file(", "download.file"},
    {"sys.getenv(",    "Sys.getenv"},
    {"ccall(",         "ccall"},
    {"unsafe_load(",   "unsafe_load"},
    {"env[",           "ENV"},
};

} // anonymous namespace

RC_GTEST_PROP(SandboxBlocklistPBT, RejectionReasonContainsBlockedFunctionName, ()) {
    // Pick a random pattern from the expectations list
    auto patternIdx = *rc::gen::inRange<size_t>(0, kPatternExpectations.size());
    const auto& expectation = kPatternExpectations[patternIdx];

    // Generate safe surrounding code (digits and arithmetic only)
    auto prefix = *genSafeCodeFragment();
    auto suffix = *genSafeCodeFragment();

    // Embed the single blocked pattern in surrounding safe code
    std::string code = prefix + expectation.pattern + suffix;

    auto& verifier = SandboxVerifier::GetInstance();
    std::string rejection_reason;

    bool result = verifier.ValidateFromAnySource(
        code, ExecutionSource::ExcelCell, rejection_reason);

    // Assert: code must be rejected
    RC_ASSERT(!result);

    // Assert: rejection_reason must not be empty
    RC_ASSERT(!rejection_reason.empty());

    // Assert: rejection_reason must contain the expected function name
    // Use case-insensitive search since the reason may use different casing
    std::string lower_reason = rejection_reason;
    std::transform(lower_reason.begin(), lower_reason.end(), lower_reason.begin(),
                   [](unsigned char c) { return std::tolower(c); });

    std::string lower_expected = expectation.expected_in_reason;
    std::transform(lower_expected.begin(), lower_expected.end(), lower_expected.begin(),
                   [](unsigned char c) { return std::tolower(c); });

    RC_ASSERT(lower_reason.find(lower_expected) != std::string::npos);
}
