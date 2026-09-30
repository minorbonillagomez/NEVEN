/**
 * Copyright (c) 2026 NEVEN Project
 *
 * Property-based tests for environment variable lookup priority.
 *
 * These tests use rapidcheck integrated with Google Test to verify that
 * GetNevenEnvVar correctly implements the strict priority order:
 * NEVEN_ > RJ2XCL_ > BERT_ > empty string.
 *
 * Feature: security-remediation
 * Property 9: Environment variable lookup priority
 *
 * Properties tested:
 *   P9a — All three prefixes set → returns NEVEN_ value
 *   P9b — Only RJ2XCL_ and BERT_ set → returns RJ2XCL_ value
 *   P9c — Only BERT_ set → returns BERT_ value
 *   P9d — None set → returns empty string
 *
 * **Validates: Requirements 15.3**
 */

#include <gtest/gtest.h>
#include <rapidcheck.h>
#include <rapidcheck/gtest.h>

#include "EnvService.h"

#include <string>
#include <Windows.h>

// ═══════════════════════════════════════════════════════════════════
// Helper: RAII cleanup for environment variables
// ═══════════════════════════════════════════════════════════════════

namespace {

/**
 * @brief RAII guard that removes environment variables on destruction.
 * Ensures test isolation by cleaning up all prefixed variants.
 */
class EnvVarGuard {
public:
    explicit EnvVarGuard(const std::string& base_name)
        : base_name_(base_name) {}

    ~EnvVarGuard() {
        // Remove all prefixed variants
        SetEnvironmentVariableA(("NEVEN_" + base_name_).c_str(), nullptr);
        SetEnvironmentVariableA(("RJ2XCL_" + base_name_).c_str(), nullptr);
        SetEnvironmentVariableA(("BERT_" + base_name_).c_str(), nullptr);
    }

    void SetNeven(const std::string& value) {
        SetEnvironmentVariableA(("NEVEN_" + base_name_).c_str(), value.c_str());
    }

    void SetRj2xcl(const std::string& value) {
        SetEnvironmentVariableA(("RJ2XCL_" + base_name_).c_str(), value.c_str());
    }

    void SetBert(const std::string& value) {
        SetEnvironmentVariableA(("BERT_" + base_name_).c_str(), value.c_str());
    }

private:
    std::string base_name_;
};

} // anonymous namespace

// ═══════════════════════════════════════════════════════════════════
// Generators
// ═══════════════════════════════════════════════════════════════════

namespace rc {

/**
 * @brief Generator for valid environment variable base names.
 * Produces alphanumeric strings of length 3-10 prefixed with "TEST_PBT_"
 * to avoid collisions with real environment variables.
 */
Gen<std::string> genBaseName() {
    return gen::apply(
        [](const std::string& s) {
            // Prefix with "TEST_PBT_" to avoid collisions with real env vars
            size_t len = s.size() > 10 ? 10 : s.size();
            std::string trimmed = s.substr(0, len);
            if (trimmed.size() < 3) trimmed += "XYZ";
            return "TEST_PBT_" + trimmed;
        },
        gen::container<std::string>(
            gen::elementOf(
                std::string("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789")
            )
        )
    );
}

/**
 * @brief Generator for non-empty environment variable values.
 * Produces alphanumeric strings of length 1-50.
 */
Gen<std::string> genEnvValue() {
    return gen::apply(
        [](const std::string& s) {
            // Ensure non-empty
            if (s.empty()) return std::string("default_val");
            size_t len = s.size() > 50 ? 50 : s.size();
            return s.substr(0, len);
        },
        gen::container<std::string>(
            gen::elementOf(
                std::string("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-./")
            )
        )
    );
}

} // namespace rc

// ═══════════════════════════════════════════════════════════════════
// Property 9a: All three prefixes set → returns NEVEN_ value
//
// Feature: security-remediation
// Property 9: Environment variable lookup priority
// **Validates: Requirements 15.3**
//
// For any base variable name, when NEVEN_, RJ2XCL_, and BERT_ prefixed
// variants are all set with distinct values, GetNevenEnvVar SHALL return
// the NEVEN_ prefixed value.
// ═══════════════════════════════════════════════════════════════════

RC_GTEST_PROP(EnvLookupPBT, NevenWinsOverAll, ()) {
    auto base_name = *rc::genBaseName();
    auto neven_val = *rc::genEnvValue();
    auto rj2xcl_val = *rc::genEnvValue();
    auto bert_val = *rc::genEnvValue();

    // Ensure distinct values so we can verify which one is returned
    RC_PRE(neven_val != rj2xcl_val);
    RC_PRE(neven_val != bert_val);
    RC_PRE(rj2xcl_val != bert_val);

    EnvVarGuard guard(base_name);
    guard.SetNeven(neven_val);
    guard.SetRj2xcl(rj2xcl_val);
    guard.SetBert(bert_val);

    auto result = rj2xcl::GetNevenEnvVar(base_name);

    RC_ASSERT(result == neven_val);
}

// ═══════════════════════════════════════════════════════════════════
// Property 9b: Only RJ2XCL_ and BERT_ set → returns RJ2XCL_ value
//
// Feature: security-remediation
// Property 9: Environment variable lookup priority
// **Validates: Requirements 15.3**
//
// For any base variable name, when only RJ2XCL_ and BERT_ prefixed
// variants are set (NEVEN_ is not set), GetNevenEnvVar SHALL return
// the RJ2XCL_ prefixed value.
// ═══════════════════════════════════════════════════════════════════

RC_GTEST_PROP(EnvLookupPBT, Rj2xclWinsOverBert, ()) {
    auto base_name = *rc::genBaseName();
    auto rj2xcl_val = *rc::genEnvValue();
    auto bert_val = *rc::genEnvValue();

    // Ensure distinct values
    RC_PRE(rj2xcl_val != bert_val);

    EnvVarGuard guard(base_name);
    // Do NOT set NEVEN_ — only RJ2XCL_ and BERT_
    guard.SetRj2xcl(rj2xcl_val);
    guard.SetBert(bert_val);

    auto result = rj2xcl::GetNevenEnvVar(base_name);

    RC_ASSERT(result == rj2xcl_val);
}

// ═══════════════════════════════════════════════════════════════════
// Property 9c: Only BERT_ set → returns BERT_ value
//
// Feature: security-remediation
// Property 9: Environment variable lookup priority
// **Validates: Requirements 15.3**
//
// For any base variable name, when only the BERT_ prefixed variant
// is set (NEVEN_ and RJ2XCL_ are not set), GetNevenEnvVar SHALL
// return the BERT_ prefixed value.
// ═══════════════════════════════════════════════════════════════════

RC_GTEST_PROP(EnvLookupPBT, BertReturnedWhenOnlyOption, ()) {
    auto base_name = *rc::genBaseName();
    auto bert_val = *rc::genEnvValue();

    EnvVarGuard guard(base_name);
    // Do NOT set NEVEN_ or RJ2XCL_ — only BERT_
    guard.SetBert(bert_val);

    auto result = rj2xcl::GetNevenEnvVar(base_name);

    RC_ASSERT(result == bert_val);
}

// ═══════════════════════════════════════════════════════════════════
// Property 9d: None set → returns empty string
//
// Feature: security-remediation
// Property 9: Environment variable lookup priority
// **Validates: Requirements 15.3**
//
// For any base variable name, when none of the prefixed variants
// (NEVEN_, RJ2XCL_, BERT_) are set, GetNevenEnvVar SHALL return
// an empty string.
// ═══════════════════════════════════════════════════════════════════

RC_GTEST_PROP(EnvLookupPBT, EmptyWhenNoneSet, ()) {
    auto base_name = *rc::genBaseName();

    EnvVarGuard guard(base_name);
    // Do NOT set any prefixed variant — guard destructor ensures cleanup

    auto result = rj2xcl::GetNevenEnvVar(base_name);

    RC_ASSERT(result.empty());
}
