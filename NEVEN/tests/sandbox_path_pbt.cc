/**
 * Copyright (c) 2026 NEVEN Project
 *
 * Property-based tests for SandboxVerifier execution path equivalence.
 *
 * These tests use rapidcheck integrated with Google Test to verify that
 * the SandboxVerifier produces identical verdicts regardless of the
 * ExecutionSource (ExcelCell, REPL, AutoLoader).
 *
 * Feature: security-remediation
 * Property 3: Sandbox execution path equivalence
 *
 * Properties tested:
 *   P3a — ValidateFromAnySource returns the same boolean result for all sources
 *   P3b — If blocked, rejection_reason is identical across all sources
 *
 * **Validates: Requirements 3.1, 3.2**
 */

#include <gtest/gtest.h>
#include <rapidcheck.h>
#include <rapidcheck/gtest.h>

#include "SandboxVerifier.h"

#include <string>

using rj2xcl::security::SandboxVerifier;
using rj2xcl::security::ExecutionSource;

// ═══════════════════════════════════════════════════════════════════
// Property 3: Sandbox execution path equivalence
//
// Feature: security-remediation
// Property 3: Sandbox execution path equivalence
// **Validates: Requirements 3.1, 3.2**
//
// For any code string, calling ValidateFromAnySource with different
// ExecutionSource values (ExcelCell, REPL, AutoLoader) SHALL produce
// the same boolean result. Additionally, if the code is blocked, the
// rejection_reason SHALL be identical across all sources.
// ═══════════════════════════════════════════════════════════════════

RC_GTEST_PROP(SandboxPathPBT, SameVerdictRegardlessOfSource, ()) {
    // Generator: random code strings (arbitrary content)
    auto code = *rc::gen::string<std::string>();

    auto& verifier = SandboxVerifier::GetInstance();

    // Validate from each source
    std::string reason_excel;
    std::string reason_repl;
    std::string reason_autoloader;

    bool result_excel = verifier.ValidateFromAnySource(
        code, ExecutionSource::ExcelCell, reason_excel);
    bool result_repl = verifier.ValidateFromAnySource(
        code, ExecutionSource::REPL, reason_repl);
    bool result_autoloader = verifier.ValidateFromAnySource(
        code, ExecutionSource::AutoLoader, reason_autoloader);

    // Assert: same boolean verdict regardless of source
    RC_ASSERT(result_excel == result_repl);
    RC_ASSERT(result_excel == result_autoloader);

    // Assert: if blocked, rejection_reason is the same across all sources
    if (!result_excel) {
        RC_ASSERT(reason_excel == reason_repl);
        RC_ASSERT(reason_excel == reason_autoloader);
    }
}

// ═══════════════════════════════════════════════════════════════════
// Property 6: Sandbox verification idempotence
//
// Feature: security-remediation
// Property 6: Sandbox verification idempotence
// **Validates: Requirements 3.8**
//
// For any code string, calling ValidateFromAnySource twice with the
// same input SHALL produce the same boolean result and the same
// rejection_reason string.
// ═══════════════════════════════════════════════════════════════════

RC_GTEST_PROP(SandboxPathPBT, VerificationIsIdempotent, ()) {
    // Generator: arbitrary strings
    auto code = *rc::gen::string<std::string>();

    auto& verifier = SandboxVerifier::GetInstance();

    // First call
    std::string reason_first;
    bool result_first = verifier.ValidateFromAnySource(
        code, ExecutionSource::ExcelCell, reason_first);

    // Second call with identical input
    std::string reason_second;
    bool result_second = verifier.ValidateFromAnySource(
        code, ExecutionSource::ExcelCell, reason_second);

    // Assert: same boolean result on repeated calls
    RC_ASSERT(result_first == result_second);

    // Assert: same rejection_reason string on repeated calls
    RC_ASSERT(reason_first == reason_second);
}
