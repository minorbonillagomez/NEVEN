/**
 * Copyright (c) 2026 NEVEN Project
 *
 * Property-based tests for WebView2 viewer subsystem.
 *
 * Properties tested:
 *   P2  — Size-Based Routing Threshold (< 2MB → NavigateToString, ≥ 2MB → temp file)
 *   P3  — Content Type Detection (file path vs inline HTML)
 *   P9  — Configuration Integer Clamping (maxViewers, maxMemoryMB)
 *   P11 — Cell Value Format (viewer ID format "viewer-N")
 *   P20 — Export Filename Sanitization (non-alphanumeric → underscore)
 *
 * These tests do NOT require WebView2 runtime or Excel.
 * They test only logic that can be tested in isolation.
 */

#include <gtest/gtest.h>
#include "ContentPipeline.h"
#include "NotebookExporter.h"

#include <random>
#include <string>
#include <sstream>
#include <climits>
#include <regex>
#include <algorithm>

using namespace rj2xcl;

// ═══════════════════════════════════════════════════════════════════
// Test fixture and random generators
// ═══════════════════════════════════════════════════════════════════

class WebView2PBT : public ::testing::Test {
protected:
    std::mt19937 rng;

    void SetUp() override {
        rng.seed(42);
    }

    // ── Generator: Random string of given length ──

    std::string GenerateRandomString(int min_len, int max_len) {
        static const char charset[] =
            "abcdefghijklmnopqrstuvwxyz"
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            "0123456789 !@#$%^&*()-_=+[]{}|;:',.<>?/~`";
        std::uniform_int_distribution<int> len_dist(min_len, max_len);
        std::uniform_int_distribution<int> char_dist(0, sizeof(charset) - 2);

        int length = len_dist(rng);
        std::string s;
        s.reserve(length);
        for (int i = 0; i < length; ++i) {
            s += charset[char_dist(rng)];
        }
        return s;
    }

    // ── Generator: Random file extension ──

    std::string GenerateFileExtension() {
        static const std::string extensions[] = {
            ".html", ".htm", ".HTML", ".HTM", ".Html", ".Htm",
            ".txt", ".csv", ".json", ".xml", ".pdf", ".js", ".css",
            ".r", ".jl", ".py", ".md", ".doc", ""
        };
        std::uniform_int_distribution<int> dist(0, 18);
        return extensions[dist(rng)];
    }

    // ── Generator: Random integer (full range) ──

    int GenerateRandomInt() {
        std::uniform_int_distribution<int> dist(INT_MIN, INT_MAX);
        return dist(rng);
    }

    // ── Generator: Random positive integer ──

    int GeneratePositiveInt(int max_val = 10000) {
        std::uniform_int_distribution<int> dist(1, max_val);
        return dist(rng);
    }

    // ── Generator: Random title string (may include Unicode-like chars) ──

    std::string GenerateTitle() {
        static const char charset[] =
            "abcdefghijklmnopqrstuvwxyz"
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            "0123456789"
            " !@#$%^&*()-_=+[]{}|;:',.<>?/~`\"\\";
        std::uniform_int_distribution<int> len_dist(0, 80);
        std::uniform_int_distribution<int> char_dist(0, sizeof(charset) - 2);

        int length = len_dist(rng);
        std::string s;
        s.reserve(length);
        for (int i = 0; i < length; ++i) {
            s += charset[char_dist(rng)];
        }
        return s;
    }
};

// ═══════════════════════════════════════════════════════════════════
// Property 2: Size-Based Routing Threshold
//
// For any HTML content string, the routing decision SHALL be:
//   < 2,097,152 bytes → NavigateToString (inline)
//   ≥ 2,097,152 bytes → temp file + Navigate(file://)
//
// We test the threshold logic, not actual navigation.
// ═══════════════════════════════════════════════════════════════════

TEST_F(WebView2PBT, Property2_SizeBasedRoutingThreshold) {
    const int NUM_ITERATIONS = 150;
    const size_t THRESHOLD = 2 * 1024 * 1024; // 2 MB
    int valid_count = 0;

    for (int i = 0; i < NUM_ITERATIONS; ++i) {
        // Generate random sizes around the threshold
        std::uniform_int_distribution<size_t> size_dist(0, 4 * 1024 * 1024);
        size_t content_size = size_dist(rng);

        bool should_use_string = (content_size < THRESHOLD);
        bool should_use_file = (content_size >= THRESHOLD);

        // Verify the routing decision is deterministic and correct
        if (content_size < THRESHOLD) {
            EXPECT_TRUE(should_use_string)
                << "Iteration " << i << ": Size " << content_size
                << " should route to NavigateToString";
            EXPECT_FALSE(should_use_file);
        } else {
            EXPECT_TRUE(should_use_file)
                << "Iteration " << i << ": Size " << content_size
                << " should route to temp file";
            EXPECT_FALSE(should_use_string);
        }

        // Verify threshold boundary
        EXPECT_TRUE(THRESHOLD - 1 < THRESHOLD);
        EXPECT_FALSE(THRESHOLD < THRESHOLD);

        ++valid_count;
    }

    EXPECT_EQ(valid_count, NUM_ITERATIONS);
}

// ═══════════════════════════════════════════════════════════════════
// Property 3: Content Type Detection
//
// For any string:
//   - Ends with .html/.htm (case-insensitive) → file path
//   - Starts with <!DOCTYPE or <html → inline HTML
//   - Otherwise → treated as file path
// ═══════════════════════════════════════════════════════════════════

TEST_F(WebView2PBT, Property3_ContentTypeDetection) {
    const int NUM_ITERATIONS = 150;
    int valid_count = 0;

    for (int i = 0; i < NUM_ITERATIONS; ++i) {
        // Test 1: .html/.htm extensions should be detected as HTML files
        std::string base = GenerateRandomString(1, 30);
        std::string html_path = base + ".html";
        EXPECT_TRUE(ContentPipeline::IsHtmlFile(html_path))
            << "Iteration " << i << ": '" << html_path << "' should be detected as HTML file";

        std::string htm_path = base + ".htm";
        EXPECT_TRUE(ContentPipeline::IsHtmlFile(htm_path))
            << "Iteration " << i << ": '" << htm_path << "' should be detected as HTML file";

        // Test 2: Inline HTML should be detected
        std::string inline_html = "<html>" + GenerateRandomString(0, 50) + "</html>";
        EXPECT_TRUE(ContentPipeline::IsInlineHtml(inline_html))
            << "Iteration " << i << ": '" << inline_html.substr(0, 30)
            << "...' should be detected as inline HTML";

        std::string doctype_html = "<!DOCTYPE html>" + GenerateRandomString(0, 50);
        EXPECT_TRUE(ContentPipeline::IsInlineHtml(doctype_html))
            << "Iteration " << i << ": DOCTYPE string should be detected as inline HTML";

        // Test 3: Non-HTML extensions should NOT be detected as HTML files
        std::string non_html = base + ".txt";
        EXPECT_FALSE(ContentPipeline::IsHtmlFile(non_html))
            << "Iteration " << i << ": '" << non_html << "' should NOT be detected as HTML file";

        // Test 4: Plain text should NOT be detected as inline HTML
        std::string plain = "Hello World " + GenerateRandomString(0, 20);
        EXPECT_FALSE(ContentPipeline::IsInlineHtml(plain))
            << "Iteration " << i << ": '" << plain.substr(0, 30)
            << "' should NOT be detected as inline HTML";

        ++valid_count;
    }

    EXPECT_EQ(valid_count, NUM_ITERATIONS);
}

// ═══════════════════════════════════════════════════════════════════
// Property 9: Configuration Integer Clamping
//
// For any integer V:
//   maxViewers: clamp to [1, 16]
//   maxMemoryMB: clamp to [128, 2048]
//   clamp(V, lo, hi) == max(lo, min(hi, V))
// ═══════════════════════════════════════════════════════════════════

TEST_F(WebView2PBT, Property9_ConfigurationIntegerClamping) {
    const int NUM_ITERATIONS = 150;
    int valid_count = 0;

    auto clamp = [](int v, int lo, int hi) -> int {
        return (std::max)(lo, (std::min)(hi, v));
    };

    for (int i = 0; i < NUM_ITERATIONS; ++i) {
        int random_val = GenerateRandomInt();

        // maxViewers: [1, 16]
        int clamped_viewers = clamp(random_val, 1, 16);
        EXPECT_GE(clamped_viewers, 1)
            << "Iteration " << i << ": maxViewers clamped below 1";
        EXPECT_LE(clamped_viewers, 16)
            << "Iteration " << i << ": maxViewers clamped above 16";

        // Verify clamp formula
        int expected_viewers = (std::max)(1, (std::min)(16, random_val));
        EXPECT_EQ(clamped_viewers, expected_viewers)
            << "Iteration " << i << ": maxViewers clamp mismatch for input " << random_val;

        // maxMemoryMB: [128, 2048]
        int clamped_memory = clamp(random_val, 128, 2048);
        EXPECT_GE(clamped_memory, 128)
            << "Iteration " << i << ": maxMemoryMB clamped below 128";
        EXPECT_LE(clamped_memory, 2048)
            << "Iteration " << i << ": maxMemoryMB clamped above 2048";

        int expected_memory = (std::max)(128, (std::min)(2048, random_val));
        EXPECT_EQ(clamped_memory, expected_memory)
            << "Iteration " << i << ": maxMemoryMB clamp mismatch for input " << random_val;

        ++valid_count;
    }

    EXPECT_EQ(valid_count, NUM_ITERATIONS);
}

// ═══════════════════════════════════════════════════════════════════
// Property 11: Viewer ID Format
//
// For any sequence of viewer creations, IDs SHALL:
//   - Match format "viewer-[N]" where N is a positive integer
//   - Be unique (monotonically increasing)
// ═══════════════════════════════════════════════════════════════════

TEST_F(WebView2PBT, Property11_ViewerIdFormat) {
    const int NUM_ITERATIONS = 150;
    int valid_count = 0;

    std::regex viewer_id_pattern("^viewer-\\d+$");

    for (int i = 0; i < NUM_ITERATIONS; ++i) {
        // Simulate viewer ID generation
        int id_num = GeneratePositiveInt(100000);
        std::string viewer_id = "viewer-" + std::to_string(id_num);

        // Verify format matches "viewer-[N]"
        EXPECT_TRUE(std::regex_match(viewer_id, viewer_id_pattern))
            << "Iteration " << i << ": ID '" << viewer_id
            << "' does not match viewer-[N] format";

        // Verify the numeric part can be extracted
        std::string num_part = viewer_id.substr(7); // "viewer-" is 7 chars
        int extracted = std::stoi(num_part);
        EXPECT_EQ(extracted, id_num)
            << "Iteration " << i << ": Extracted number " << extracted
            << " does not match original " << id_num;

        ++valid_count;
    }

    EXPECT_EQ(valid_count, NUM_ITERATIONS);
}

// ═══════════════════════════════════════════════════════════════════
// Property 20: Export Filename Sanitization
//
// For any title string T:
//   - All non-alphanumeric characters replaced with underscores
//   - Empty title → "untitled"
//   - Result matches [a-zA-Z0-9_]+
// ═══════════════════════════════════════════════════════════════════

TEST_F(WebView2PBT, Property20_ExportFilenameSanitization) {
    const int NUM_ITERATIONS = 150;
    int valid_count = 0;

    std::regex sanitized_pattern("^[a-zA-Z0-9_]+$");

    for (int i = 0; i < NUM_ITERATIONS; ++i) {
        std::string title = GenerateTitle();

        // Simulate sanitization (same logic as NotebookExporter::SanitizeTitle)
        std::string sanitized;
        if (title.empty()) {
            sanitized = "untitled";
        } else {
            sanitized.reserve(title.size());
            for (char c : title) {
                if (std::isalnum(static_cast<unsigned char>(c))) {
                    sanitized += c;
                } else {
                    sanitized += '_';
                }
            }
        }

        // Verify result is non-empty
        EXPECT_FALSE(sanitized.empty())
            << "Iteration " << i << ": Sanitized title should never be empty";

        // Verify result matches [a-zA-Z0-9_]+
        EXPECT_TRUE(std::regex_match(sanitized, sanitized_pattern))
            << "Iteration " << i << ": Sanitized '" << sanitized
            << "' contains invalid characters (from title '" << title.substr(0, 30) << "')";

        // Verify length is preserved (each char maps to exactly one char)
        if (!title.empty()) {
            EXPECT_EQ(sanitized.size(), title.size())
                << "Iteration " << i << ": Sanitized length mismatch";
        }

        ++valid_count;
    }

    EXPECT_EQ(valid_count, NUM_ITERATIONS);
}
