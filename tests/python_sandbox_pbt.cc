/**
 * Copyright (c) 2026 NEVEN Project
 *
 * Property-based tests for the Python sandbox patterns in SandboxVerifier.
 *
 * These tests use custom random generators within GTest to verify correctness
 * properties across many randomized inputs (minimum 100 iterations each).
 *
 * Properties tested:
 *   P5 — Sandbox blocks all Python dangerous patterns (with whitespace/case variation)
 *   P7 — Sandbox allows safe Python code
 *   P8 — Sandbox idempotence (same result on consecutive calls)
 */

#include <gtest/gtest.h>
#include "SandboxVerifier.h"

#include <random>
#include <string>
#include <vector>
#include <algorithm>
#include <sstream>

using rj2xcl::security::SandboxVerifier;

// ═══════════════════════════════════════════════════════════════════
// Task 9.1 — Test fixture and random generators
// ═══════════════════════════════════════════════════════════════════

class PythonSandboxPBT : public ::testing::Test {
protected:
    SandboxVerifier& sandbox = SandboxVerifier::GetInstance();
    std::mt19937 rng;

    void SetUp() override {
        // Fixed seed for reproducibility; change to std::random_device{}() for exploration
        rng.seed(42);
    }

    // ── Blocked patterns (from SandboxVerifier.cc python_blocked) ──

    static const std::vector<std::string>& GetBlockedPatterns() {
        static const std::vector<std::string> patterns = {
            // Shell execution
            "os.system(",
            "os.popen(",
            "subprocess.call(",
            "subprocess.run(",
            "subprocess.popen(",
            "subprocess.check_output(",
            "subprocess.check_call(",
            // File manipulation
            "os.remove(",
            "os.unlink(",
            "os.rmdir(",
            "os.rename(",
            "shutil.rmtree(",
            "shutil.move(",
            "shutil.copy(",
            // Dynamic code execution
            "exec(",
            "eval(",
            "compile(",
            "__import__(",
            "importlib.import_module(",
            // Native/unsafe
            "ctypes.cdll",
            "ctypes.windll",
            // Network
            "urllib.request.urlopen(",
            "socket.socket(",
            "http.client.httpconnection(",
            // Environment manipulation
            "os.environ[",
            "os.putenv(",
            "os.chdir(",
        };
        return patterns;
    }

    // ── Safe code templates ──────────────────────────────────────

    static const std::vector<std::string>& GetSafeTemplates() {
        static const std::vector<std::string> templates = {
            // Arithmetic
            "x = 42 + 3.14",
            "y = x * 2 - 1",
            "z = (a + b) / c",
            "result = 100 % 7",
            "power = 2 ** 10",
            "neg = -42",
            "total = 1 + 2 + 3 + 4 + 5",
            // Assignments
            "name = 'hello'",
            "data = [1, 2, 3]",
            "result = True",
            "value = None",
            "pi = 3.14159",
            "count = 0",
            "flag = False",
            "items = {'a': 1, 'b': 2}",
            // Safe function calls (no blocked patterns)
            "len([1,2,3])",
            "range(10)",
            "print('hello')",
            "str(42)",
            "int('42')",
            "float('3.14')",
            "abs(-5)",
            "max(1,2,3)",
            "min(1,2,3)",
            "sum([1,2,3])",
            "sorted([3,1,2])",
            "type(x)",
            "round(3.14159, 2)",
            "pow(2, 10)",
            "divmod(17, 5)",
            "bool(1)",
            "list(range(5))",
            "tuple([1,2,3])",
            "dict(a=1, b=2)",
            "set([1,2,2,3])",
            "frozenset([1,2,3])",
            "repr(42)",
            "hash('hello')",
            "id(x)",
            "isinstance(x, int)",
            "issubclass(bool, int)",
            "zip([1,2], [3,4])",
            "map(str, [1,2,3])",
            "filter(None, [0,1,2])",
            "reversed([1,2,3])",
            "enumerate([10,20,30])",
            // List comprehensions
            "[x**2 for x in range(10)]",
            "[i for i in data if i > 0]",
            "[str(n) for n in range(5)]",
            "[[i*j for j in range(3)] for i in range(3)]",
            // String operations
            "'hello'.upper()",
            "'world'.strip()",
            "f'value={x}'",
            "'hello' + ' ' + 'world'",
            "'abc'.replace('a', 'z')",
            "'hello world'.split()",
            "', '.join(['a', 'b', 'c'])",
            "'hello'.startswith('he')",
            "'hello'.endswith('lo')",
            "'hello'.find('ll')",
            "'hello'.count('l')",
            "'hello'.capitalize()",
            "'hello'.title()",
            "'  hello  '.strip()",
            "'hello'.center(20)",
            "'hello'.ljust(20)",
            "'hello'.rjust(20)",
            "'hello'.zfill(10)",
            "'hello'.isalpha()",
            "'123'.isdigit()",
            // Imports (safe ones — no blocked patterns)
            "import pandas as pd",
            "import numpy as np",
            "from datetime import datetime",
            "import math",
            "import json",
            "import csv",
            "import re",
            "import collections",
            "import itertools",
            "import functools",
            "import statistics",
            "import decimal",
            "import fractions",
            "import random",
            "import string",
            "import textwrap",
            "import copy",
            "import pprint",
            "import operator",
            // Math operations
            "math.sqrt(144)",
            "math.pi",
            "math.sin(0.5)",
            "math.cos(0.5)",
            "math.log(10)",
            "math.floor(3.7)",
            "math.ceil(3.2)",
            // Pandas/numpy style (safe)
            "df.describe()",
            "df.head()",
            "df.tail()",
            "df.shape",
            "df.columns",
            "df.dtypes",
            "df.info()",
            "df.mean()",
            "df.std()",
            "df.corr()",
            "np.mean([1,2,3])",
            "np.std([1,2,3])",
            "np.array([1,2,3])",
            "np.zeros(10)",
            "np.ones(10)",
            "np.linspace(0, 1, 100)",
            "np.arange(0, 10, 0.5)",
        };
        return templates;
    }

    // ── Helper: Insert random whitespace into a string ───────────

    std::string InsertRandomWhitespace(const std::string& str) {
        std::string result;
        result.reserve(str.size() * 2);
        std::uniform_int_distribution<int> dist(0, 4);
        for (char c : str) {
            // Randomly insert whitespace before the character
            if (dist(rng) == 0) {
                int ws_type = dist(rng);
                if (ws_type <= 1) {
                    result += ' ';
                } else if (ws_type == 2) {
                    result += '\t';
                } else {
                    result += "  ";
                }
            }
            result += c;
        }
        return result;
    }

    // ── Helper: Random case variation ────────────────────────────

    std::string RandomCaseVariation(const std::string& str) {
        std::string result = str;
        std::uniform_int_distribution<int> dist(0, 2);
        for (char& c : result) {
            if (std::isalpha(static_cast<unsigned char>(c))) {
                int choice = dist(rng);
                if (choice == 0) {
                    c = std::toupper(static_cast<unsigned char>(c));
                } else if (choice == 1) {
                    c = std::tolower(static_cast<unsigned char>(c));
                }
                // choice == 2: keep original
            }
        }
        return result;
    }

    // ── Generator: Blocked code with random variation ────────────

    std::string GenerateBlockedCode() {
        const auto& patterns = GetBlockedPatterns();
        std::uniform_int_distribution<size_t> pattern_dist(0, patterns.size() - 1);
        std::string pattern = patterns[pattern_dist(rng)];

        // Apply random whitespace insertion
        std::string varied = InsertRandomWhitespace(pattern);

        // Apply random case variation
        varied = RandomCaseVariation(varied);

        // Wrap in realistic code context
        std::uniform_int_distribution<int> context_dist(0, 4);
        int context = context_dist(rng);
        switch (context) {
            case 0:
                return "result = " + varied + "'arg')";
            case 1:
                return "x = " + varied + "'test')";
            case 2:
                return varied + "'hello')";
            case 3:
                return "if True: " + varied + "'cmd')";
            case 4:
                return "data = " + varied + "'value')";
            default:
                return varied + "'arg')";
        }
    }

    // ── Generator: Safe Python code ──────────────────────────────

    std::string GenerateSafeCode() {
        const auto& templates = GetSafeTemplates();
        std::uniform_int_distribution<size_t> tmpl_dist(0, templates.size() - 1);

        // Pick a random safe template
        std::string code = templates[tmpl_dist(rng)];

        // Optionally combine multiple safe templates
        std::uniform_int_distribution<int> combine_dist(0, 3);
        int combine = combine_dist(rng);
        if (combine == 0) {
            // Combine two safe templates with newline
            std::string second = templates[tmpl_dist(rng)];
            code = code + "\n" + second;
        }

        return code;
    }

    // ── Generator: Random code (mix of safe and unsafe) ──────────

    std::string GenerateRandomCode() {
        std::uniform_int_distribution<int> dist(0, 1);
        if (dist(rng) == 0) {
            return GenerateSafeCode();
        } else {
            return GenerateBlockedCode();
        }
    }
};

// ═══════════════════════════════════════════════════════════════════
// Task 9.2 — Property 5: Sandbox blocks all Python dangerous patterns
//
// Feature: python-integration
// Property 5: Sandbox blocks all Python dangerous patterns
// **Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 13.5**
//
// For any code string containing a blocked Python pattern (with random
// whitespace/case variation), ValidateCodeForExecution SHALL return
// false with a non-empty rejection reason.
// ═══════════════════════════════════════════════════════════════════

TEST_F(PythonSandboxPBT, Property5_BlocksAllDangerousPatterns) {
    const int NUM_ITERATIONS = 150;
    int blocked_count = 0;

    for (int i = 0; i < NUM_ITERATIONS; ++i) {
        std::string code = GenerateBlockedCode();
        std::string reason;
        bool allowed = sandbox.ValidateCodeForExecution(code, reason);

        EXPECT_FALSE(allowed)
            << "Iteration " << i << ": Expected blocked but was allowed.\n"
            << "  Generated code: \"" << code << "\"\n"
            << "  Rejection reason: \"" << reason << "\"";

        if (!allowed) {
            EXPECT_FALSE(reason.empty())
                << "Iteration " << i << ": Blocked but rejection reason is empty.\n"
                << "  Generated code: \"" << code << "\"";
            ++blocked_count;
        }
    }

    // Sanity check: all iterations should have been blocked
    EXPECT_EQ(blocked_count, NUM_ITERATIONS)
        << "Not all generated blocked patterns were rejected.";
}

// ═══════════════════════════════════════════════════════════════════
// Task 9.3 — Property 7: Sandbox allows safe Python code
//
// Feature: python-integration
// Property 7: Sandbox allows safe Python code
// **Validates: Requirements 7.9**
//
// For any safe Python code string (arithmetic, assignments, safe
// function calls), ValidateCodeForExecution SHALL return true with
// an empty rejection reason.
// ═══════════════════════════════════════════════════════════════════

TEST_F(PythonSandboxPBT, Property7_AllowsSafePythonCode) {
    const int NUM_ITERATIONS = 150;
    int allowed_count = 0;

    for (int i = 0; i < NUM_ITERATIONS; ++i) {
        std::string code = GenerateSafeCode();
        std::string reason;
        bool allowed = sandbox.ValidateCodeForExecution(code, reason);

        EXPECT_TRUE(allowed)
            << "Iteration " << i << ": Expected allowed but was blocked.\n"
            << "  Generated code: \"" << code << "\"\n"
            << "  Rejection reason: \"" << reason << "\"";

        if (allowed) {
            EXPECT_TRUE(reason.empty())
                << "Iteration " << i << ": Allowed but rejection reason is non-empty.\n"
                << "  Generated code: \"" << code << "\"\n"
                << "  Rejection reason: \"" << reason << "\"";
            ++allowed_count;
        }
    }

    // Sanity check: all iterations should have been allowed
    EXPECT_EQ(allowed_count, NUM_ITERATIONS)
        << "Not all generated safe code strings were accepted.";
}

// ═══════════════════════════════════════════════════════════════════
// Task 9.4 — Property 8: Sandbox idempotence
//
// Feature: python-integration
// Property 8: Sandbox idempotence
// **Validates: Requirements 13.4**
//
// For any Python code string (safe or unsafe), calling
// ValidateCodeForExecution twice with the same input SHALL produce
// identical results — same boolean return and same rejection reason.
// ═══════════════════════════════════════════════════════════════════

TEST_F(PythonSandboxPBT, Property8_IdempotentValidation) {
    const int NUM_ITERATIONS = 150;
    int consistent_count = 0;

    for (int i = 0; i < NUM_ITERATIONS; ++i) {
        std::string code = GenerateRandomCode();

        // First call
        std::string reason1;
        bool result1 = sandbox.ValidateCodeForExecution(code, reason1);

        // Second call with the same input
        std::string reason2;
        bool result2 = sandbox.ValidateCodeForExecution(code, reason2);

        EXPECT_EQ(result1, result2)
            << "Iteration " << i << ": Non-idempotent boolean result.\n"
            << "  Code: \"" << code << "\"\n"
            << "  First call: " << (result1 ? "allowed" : "blocked") << "\n"
            << "  Second call: " << (result2 ? "allowed" : "blocked") << "\n";

        EXPECT_EQ(reason1, reason2)
            << "Iteration " << i << ": Non-idempotent rejection reason.\n"
            << "  Code: \"" << code << "\"\n"
            << "  First reason: \"" << reason1 << "\"\n"
            << "  Second reason: \"" << reason2 << "\"\n";

        if (result1 == result2 && reason1 == reason2) {
            ++consistent_count;
        }
    }

    // Sanity check: all iterations should have been consistent
    EXPECT_EQ(consistent_count, NUM_ITERATIONS)
        << "Not all iterations produced idempotent results.";
}
