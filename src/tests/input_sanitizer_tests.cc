/**
 * Copyright (c) 2026 NEVEN Project
 *
 * Unit tests for InputSanitizer.
 * Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 1.6
 */

#include <gtest/gtest.h>
#include "InputSanitizer.h"

#include <string>

namespace rj2xcl {
namespace security {

class InputSanitizerTests : public ::testing::Test {
protected:
    // Helper to check that a ValidationResult is invalid
    void ExpectInvalid(const InputSanitizer::ValidationResult& result) {
        EXPECT_FALSE(result.is_valid);
        EXPECT_FALSE(result.error_message.empty());
    }

    // Helper to check that a ValidationResult is valid
    void ExpectValid(const InputSanitizer::ValidationResult& result) {
        EXPECT_TRUE(result.is_valid);
        EXPECT_TRUE(result.error_message.empty());
    }
};

// ---------------------------------------------------------------------------
// ValidatePath — empty and length checks
// ---------------------------------------------------------------------------

TEST_F(InputSanitizerTests, ValidatePath_EmptyPath_ReturnsInvalid) {
    auto result = InputSanitizer::ValidatePath("");
    ExpectInvalid(result);
}

TEST_F(InputSanitizerTests, ValidatePath_ExceedsMaxPath_ReturnsInvalid) {
    // MAX_PATH on Windows is 260 characters; create a string of 261 chars
    std::string long_path(261, 'A');
    auto result = InputSanitizer::ValidatePath(long_path);
    ExpectInvalid(result);
}

// ---------------------------------------------------------------------------
// ValidatePath — valid paths
// ---------------------------------------------------------------------------

TEST_F(InputSanitizerTests, ValidatePath_ValidDriveLetter_ReturnsValid) {
    auto result = InputSanitizer::ValidatePath("C:\\Users\\test.txt");
    ExpectValid(result);
}

// ---------------------------------------------------------------------------
// ValidatePath — metacharacter rejection
// ---------------------------------------------------------------------------

TEST_F(InputSanitizerTests, ValidatePath_MetacharAmpersand_ReturnsInvalid) {
    auto result = InputSanitizer::ValidatePath("C:\\Users\\file & del.txt");
    ExpectInvalid(result);
    EXPECT_EQ(result.first_invalid_char, '&');
}

TEST_F(InputSanitizerTests, ValidatePath_MetacharPipe_ReturnsInvalid) {
    auto result = InputSanitizer::ValidatePath("C:\\Users\\file|pipe.txt");
    ExpectInvalid(result);
    EXPECT_EQ(result.first_invalid_char, '|');
}

TEST_F(InputSanitizerTests, ValidatePath_MetacharSemicolon_ReturnsInvalid) {
    auto result = InputSanitizer::ValidatePath("C:\\Users\\file;cmd.txt");
    ExpectInvalid(result);
    EXPECT_EQ(result.first_invalid_char, ';');
}

TEST_F(InputSanitizerTests, ValidatePath_MetacharBacktick_ReturnsInvalid) {
    auto result = InputSanitizer::ValidatePath("C:\\Users\\file`cmd.txt");
    ExpectInvalid(result);
    EXPECT_EQ(result.first_invalid_char, '`');
}

TEST_F(InputSanitizerTests, ValidatePath_MetacharAngleBrackets_ReturnsInvalid) {
    auto result_lt = InputSanitizer::ValidatePath("C:\\Users\\file<cmd.txt");
    ExpectInvalid(result_lt);
    EXPECT_EQ(result_lt.first_invalid_char, '<');

    auto result_gt = InputSanitizer::ValidatePath("C:\\Users\\file>cmd.txt");
    ExpectInvalid(result_gt);
    EXPECT_EQ(result_gt.first_invalid_char, '>');
}

TEST_F(InputSanitizerTests, ValidatePath_MetacharNewline_ReturnsInvalid) {
    auto result_lf = InputSanitizer::ValidatePath("C:\\Users\\file\ncmd.txt");
    ExpectInvalid(result_lf);
    EXPECT_EQ(result_lf.first_invalid_char, '\n');

    auto result_cr = InputSanitizer::ValidatePath("C:\\Users\\file\rcmd.txt");
    ExpectInvalid(result_cr);
    EXPECT_EQ(result_cr.first_invalid_char, '\r');
}

TEST_F(InputSanitizerTests, ValidatePath_MetacharPercent_ReturnsInvalid) {
    auto result = InputSanitizer::ValidatePath("C:\\Users\\%SYSTEMROOT%.txt");
    ExpectInvalid(result);
    EXPECT_EQ(result.first_invalid_char, '%');
}

// ---------------------------------------------------------------------------
// ValidateArgument — metacharacter rejection
// ---------------------------------------------------------------------------

TEST_F(InputSanitizerTests, ValidateArgument_MetacharQuote_ReturnsInvalid) {
    auto result = InputSanitizer::ValidateArgument("arg\"injection");
    ExpectInvalid(result);
    EXPECT_EQ(result.first_invalid_char, '"');
}

// ---------------------------------------------------------------------------
// BuildSafeCommandLine — CreateProcess separation
// ---------------------------------------------------------------------------

TEST_F(InputSanitizerTests, BuildSafeCommandLine_SeparatesAppNameFromCmdLine) {
    std::string exe = "C:\\Program Files\\app.exe";
    std::vector<std::string> args = {"arg1", "arg2"};

    auto [app_name, cmd_line] = InputSanitizer::BuildSafeCommandLine(exe, args);

    // lpApplicationName should be the raw executable path
    EXPECT_EQ(app_name, exe);

    // lpCommandLine should have the executable quoted as argv[0] plus arguments
    EXPECT_FALSE(cmd_line.empty());
    // The command line must start with the quoted executable
    EXPECT_EQ(cmd_line.substr(0, 1), "\"");
    // Both arguments should appear quoted in the command line
    EXPECT_NE(cmd_line.find("\"arg1\""), std::string::npos);
    EXPECT_NE(cmd_line.find("\"arg2\""), std::string::npos);
}

TEST_F(InputSanitizerTests, BuildSafeCommandLine_InvalidExecutable_ReturnsEmpty) {
    // Executable with metacharacter should fail validation
    std::string exe = "C:\\Users\\app|inject.exe";
    std::vector<std::string> args = {"safe_arg"};

    auto [app_name, cmd_line] = InputSanitizer::BuildSafeCommandLine(exe, args);

    EXPECT_TRUE(app_name.empty());
    EXPECT_TRUE(cmd_line.empty());
}

TEST_F(InputSanitizerTests, BuildSafeCommandLine_InvalidArgument_ReturnsEmpty) {
    std::string exe = "C:\\Program Files\\app.exe";
    std::vector<std::string> args = {"safe", "bad&arg"};

    auto [app_name, cmd_line] = InputSanitizer::BuildSafeCommandLine(exe, args);

    EXPECT_TRUE(app_name.empty());
    EXPECT_TRUE(cmd_line.empty());
}

// ---------------------------------------------------------------------------
// SanitizePath — removal and idempotence
// ---------------------------------------------------------------------------

TEST_F(InputSanitizerTests, SanitizePath_RemovesMetachars) {
    std::string dirty = "C:\\Users\\file&|;<>`\n\r%.txt";
    std::string sanitized = InputSanitizer::SanitizePath(dirty);

    // All metacharacters should be stripped; only allowed chars remain
    EXPECT_EQ(sanitized, "C:\\Users\\file.txt");
}

TEST_F(InputSanitizerTests, SanitizePath_Idempotent) {
    std::string dirty = "C:\\Users\\bad;path|here.txt";
    std::string first_pass = InputSanitizer::SanitizePath(dirty);
    std::string second_pass = InputSanitizer::SanitizePath(first_pass);

    EXPECT_EQ(first_pass, second_pass);
}

} // namespace security
} // namespace rj2xcl
