/**
 * Copyright (c) 2026 NEVEN Project
 *
 * Property-based tests for InputSanitizer allowlist correctness.
 *
 * These tests use rapidcheck integrated with Google Test to verify that
 * the InputSanitizer correctly accepts/rejects strings based on character
 * allowlists across many randomized inputs (minimum 100 iterations).
 *
 * Feature: security-remediation
 * Property 1: allowlist correctness
 *
 * Properties tested:
 *   P1a — ValidatePath accepts iff ALL characters are in the path allowlist
 *   P1b — ValidatePath rejects iff ANY character is outside the path allowlist
 *   P1c — ValidateArgument accepts iff ALL characters are in the argument allowlist
 *   P1d — ValidateArgument rejects iff ANY character is outside the argument allowlist
 *
 * **Validates: Requirements 1.1, 1.2, 1.3, 1.5**
 */

#include <gtest/gtest.h>
#include <rapidcheck.h>
#include <rapidcheck/gtest.h>

#include "Security/InputSanitizer.h"

#include <string>
#include <algorithm>

using rj2xcl::security::InputSanitizer;

// ═══════════════════════════════════════════════════════════════════
// Helper: Reference allowlist checkers (independent of implementation)
// ═══════════════════════════════════════════════════════════════════

namespace {

/**
 * @brief Reference implementation of path character allowlist check.
 * Allowed: [A-Za-z0-9], \, /, ., -, _, space, :
 */
bool IsPathCharAllowed(char c) {
    if (c >= 'A' && c <= 'Z') return true;
    if (c >= 'a' && c <= 'z') return true;
    if (c >= '0' && c <= '9') return true;
    if (c == '\\' || c == '/') return true;
    if (c == '.' || c == '-' || c == '_') return true;
    if (c == ' ') return true;
    if (c == ':') return true;
    return false;
}

/**
 * @brief Reference implementation of argument character allowlist check.
 * Allowed: [A-Za-z0-9], ., -, _, space, =, \, /, :
 */
bool IsArgumentCharAllowed(char c) {
    if (c >= 'A' && c <= 'Z') return true;
    if (c >= 'a' && c <= 'z') return true;
    if (c >= '0' && c <= '9') return true;
    if (c == '.' || c == '-' || c == '_') return true;
    if (c == ' ') return true;
    if (c == '=') return true;
    if (c == '\\' || c == '/' || c == ':') return true;
    return false;
}

/**
 * @brief Checks if all characters in a string are in the path allowlist.
 */
bool AllCharsInPathAllowlist(const std::string& s) {
    return std::all_of(s.begin(), s.end(), IsPathCharAllowed);
}

/**
 * @brief Checks if all characters in a string are in the argument allowlist.
 */
bool AllCharsInArgumentAllowlist(const std::string& s) {
    return std::all_of(s.begin(), s.end(), IsArgumentCharAllowed);
}

} // anonymous namespace

// ═══════════════════════════════════════════════════════════════════
// Generators
// ═══════════════════════════════════════════════════════════════════

namespace rc {

/**
 * @brief Generator for strings composed entirely of path-allowed characters.
 * Produces strings of length 1..260 (MAX_PATH) with only allowed chars.
 */
Gen<std::string> genValidPathString() {
    return gen::container<std::string>(
        gen::elementOf(
            std::string("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789\\/._ -:")
        )
    );
}

/**
 * @brief Generator for strings composed entirely of argument-allowed characters.
 * Produces strings of length 1..100 with only allowed chars.
 */
Gen<std::string> genValidArgumentString() {
    return gen::container<std::string>(
        gen::elementOf(
            std::string("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._ -=\\/:"))
    );
}

/**
 * @brief Generator for characters NOT in the path allowlist.
 * These are metacharacters and control characters that should be rejected.
 */
Gen<char> genDisallowedPathChar() {
    return gen::elementOf(
        std::string("&|;`<>\"\n\r%$!@#^*(){}[]~+=?,\x01\x02\x03\x04\x05\x7f")
    );
}

/**
 * @brief Generator for characters NOT in the argument allowlist.
 * Includes metacharacters that are dangerous for command injection.
 */
Gen<char> genDisallowedArgumentChar() {
    return gen::elementOf(
        std::string("&|;`<>\"\n\r%$!@#^*(){}[]~?,\x01\x02\x03\x7f")
    );
}

/**
 * @brief Generator for strings with mixed allowed/disallowed path characters.
 * Guarantees at least one disallowed character is present.
 */
Gen<std::string> genInvalidPathString() {
    return gen::apply(
        [](const std::string& prefix, char bad, const std::string& suffix) {
            return prefix + bad + suffix;
        },
        gen::container<std::string>(
            gen::elementOf(std::string("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789\\/._ -:"))
        ),
        genDisallowedPathChar(),
        gen::container<std::string>(
            gen::elementOf(std::string("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789\\/._ -:"))
        )
    );
}

/**
 * @brief Generator for strings with mixed allowed/disallowed argument characters.
 * Guarantees at least one disallowed character is present.
 */
Gen<std::string> genInvalidArgumentString() {
    return gen::apply(
        [](const std::string& prefix, char bad, const std::string& suffix) {
            return prefix + bad + suffix;
        },
        gen::container<std::string>(
            gen::elementOf(std::string("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._ -=\\/:"))
        ),
        genDisallowedArgumentChar(),
        gen::container<std::string>(
            gen::elementOf(std::string("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._ -=\\/:"))
        )
    );
}

} // namespace rc

// ═══════════════════════════════════════════════════════════════════
// Property 1a: ValidatePath accepts strings where ALL chars are allowed
//
// Feature: security-remediation
// Property 1: allowlist correctness
// **Validates: Requirements 1.1, 1.2, 1.3, 1.5**
//
// For any non-empty string where every character is in the path
// allowlist [A-Za-z0-9\\/._- :] and length <= 260, ValidatePath
// SHALL return is_valid=true.
// ═══════════════════════════════════════════════════════════════════

RC_GTEST_PROP(InputSanitizerPBT, ValidPathAccepted, ()) {
    auto path = *rc::genValidPathString();

    // Pre-conditions: non-empty and within MAX_PATH
    RC_PRE(!path.empty());
    RC_PRE(path.size() <= 260);

    auto result = InputSanitizer::ValidatePath(path);

    RC_ASSERT(result.is_valid);
    RC_ASSERT(result.error_message.empty());
    RC_ASSERT(result.first_invalid_char == 0);
}

// ═══════════════════════════════════════════════════════════════════
// Property 1b: ValidatePath rejects strings with ANY disallowed char
//
// Feature: security-remediation
// Property 1: allowlist correctness
// **Validates: Requirements 1.1, 1.2, 1.3, 1.5**
//
// For any string containing at least one character NOT in the path
// allowlist, ValidatePath SHALL return is_valid=false and identify
// the offending character.
// ═══════════════════════════════════════════════════════════════════

RC_GTEST_PROP(InputSanitizerPBT, InvalidPathRejected, ()) {
    auto path = *rc::genInvalidPathString();

    // Pre-condition: within MAX_PATH (so rejection is due to char, not length)
    RC_PRE(path.size() <= 260);

    auto result = InputSanitizer::ValidatePath(path);

    RC_ASSERT(!result.is_valid);
    RC_ASSERT(!result.error_message.empty());
    // The first_invalid_char must actually be a disallowed character
    RC_ASSERT(!IsPathCharAllowed(result.first_invalid_char));
}

// ═══════════════════════════════════════════════════════════════════
// Property 1c: ValidateArgument accepts strings where ALL chars allowed
//
// Feature: security-remediation
// Property 1: allowlist correctness
// **Validates: Requirements 1.1, 1.2, 1.3, 1.5**
//
// For any non-empty string where every character is in the argument
// allowlist [A-Za-z0-9._ -], ValidateArgument SHALL return
// is_valid=true.
// ═══════════════════════════════════════════════════════════════════

RC_GTEST_PROP(InputSanitizerPBT, ValidArgumentAccepted, ()) {
    auto arg = *rc::genValidArgumentString();

    // Pre-condition: non-empty
    RC_PRE(!arg.empty());

    auto result = InputSanitizer::ValidateArgument(arg);

    RC_ASSERT(result.is_valid);
    RC_ASSERT(result.error_message.empty());
    RC_ASSERT(result.first_invalid_char == 0);
}

// ═══════════════════════════════════════════════════════════════════
// Property 1d: ValidateArgument rejects strings with ANY disallowed char
//
// Feature: security-remediation
// Property 1: allowlist correctness
// **Validates: Requirements 1.1, 1.2, 1.3, 1.5**
//
// For any string containing at least one character NOT in the argument
// allowlist, ValidateArgument SHALL return is_valid=false and identify
// the offending character.
// ═══════════════════════════════════════════════════════════════════

RC_GTEST_PROP(InputSanitizerPBT, InvalidArgumentRejected, ()) {
    auto arg = *rc::genInvalidArgumentString();

    auto result = InputSanitizer::ValidateArgument(arg);

    RC_ASSERT(!result.is_valid);
    RC_ASSERT(!result.error_message.empty());
    // The first_invalid_char must actually be a disallowed character
    RC_ASSERT(!IsArgumentCharAllowed(result.first_invalid_char));
}


// ═══════════════════════════════════════════════════════════════════
// Property 2: InputSanitizer idempotence
//
// Feature: security-remediation
// Property 2: idempotence
// **Validates: Requirements 1.6**
//
// For any string (including Unicode, control chars, metacharacters),
// applying SanitizePath once and then applying it again SHALL produce
// the same result: SanitizePath(SanitizePath(x)) == SanitizePath(x).
// ═══════════════════════════════════════════════════════════════════

RC_GTEST_PROP(InputSanitizerPBT, SanitizePathIdempotent, ()) {
    // Generator: arbitrary strings including Unicode, control chars, metacharacters
    auto input = *rc::gen::string<std::string>();

    auto once = InputSanitizer::SanitizePath(input);
    auto twice = InputSanitizer::SanitizePath(once);

    RC_ASSERT(twice == once);
}
