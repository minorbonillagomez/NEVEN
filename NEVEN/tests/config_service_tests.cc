/**
 * Copyright (c) 2026 NEVEN Project
 * 
 * Tests for ConfigService getters and validation.
 */

#include <gtest/gtest.h>
#include "ConfigService.h"
#include "json11/json11.hpp"

using namespace rj2xcl;

class ConfigGettersTest : public ::testing::Test {
protected:
    ConfigService& config = ConfigService::Instance();
};

// ═══════════════════════════════════════════════════════════════════
// Getter Defaults (config not loaded in test environment)
// The getters must return safe defaults when config JSON is empty.
// int_value() returns 0 for missing keys, which triggers default path.
// ═══════════════════════════════════════════════════════════════════

TEST_F(ConfigGettersTest, GetCallTimeoutMs_Returns600000WhenEmpty) {
    // With empty config, int_value() returns 0, getter returns default 600000
    DWORD timeout = config.GetCallTimeoutMs();
    EXPECT_EQ(timeout, 600000u);
}

TEST_F(ConfigGettersTest, GetMaxRetries_Returns2WhenEmpty) {
    // With empty config, int_value() returns 0, getter returns default 2
    int retries = config.GetMaxRetries();
    EXPECT_EQ(retries, 2);
}

TEST_F(ConfigGettersTest, IsSandboxEnabled_ReturnsTrueWhenEmpty) {
    // With empty config, is_bool() returns false, getter returns default true
    bool enabled = config.IsSandboxEnabled();
    EXPECT_TRUE(enabled);
}

TEST_F(ConfigGettersTest, GetGraphicsDirectory_ReturnsDefaultWhenEmpty) {
    // With empty config, string_value() returns "", getter returns hardcoded default
    std::string dir = config.GetGraphicsDirectory();
    EXPECT_FALSE(dir.empty());
    EXPECT_NE(dir.find("NEVEN"), std::string::npos);
}

// ═══════════════════════════════════════════════════════════════════
// JSON Parsing
// ═══════════════════════════════════════════════════════════════════

TEST(ConfigJsonTest, ValidConfigParsesCorrectly) {
    std::string err;
    auto json = json11::Json::parse(R"({
        "NEVEN": {
            "callTimeoutMs": 300000,
            "maxRetries": 3,
            "sandboxEnabled": true,
            "functionsDirectory": "%USERPROFILE%\\Documents\\NEVEN\\functions"
        }
    })", err, json11::COMMENTS);

    EXPECT_TRUE(err.empty());
    EXPECT_EQ(json["NEVEN"]["callTimeoutMs"].int_value(), 300000);
    EXPECT_EQ(json["NEVEN"]["maxRetries"].int_value(), 3);
    EXPECT_TRUE(json["NEVEN"]["sandboxEnabled"].bool_value());
}

TEST(ConfigJsonTest, MissingKeysReturnDefaults) {
    std::string err;
    auto json = json11::Json::parse(R"({"NEVEN": {}})", err, json11::COMMENTS);

    EXPECT_TRUE(err.empty());
    // Missing keys return 0/false/empty — getters handle defaults
    EXPECT_EQ(json["NEVEN"]["callTimeoutMs"].int_value(), 0);
    EXPECT_EQ(json["NEVEN"]["maxRetries"].int_value(), 0);
    EXPECT_FALSE(json["NEVEN"]["sandboxEnabled"].is_bool());
}

TEST(ConfigJsonTest, MalformedJsonReportsError) {
    std::string err;
    auto json = json11::Json::parse("{ not valid json !!!", err, json11::COMMENTS);
    EXPECT_FALSE(err.empty());
}

// ═══════════════════════════════════════════════════════════════════
// Path Validation Logic (unit test the concept)
// ═══════════════════════════════════════════════════════════════════

static bool ValidatePath(const std::string& path) {
    if (path.empty()) return true;
    if (path.find("..") != std::string::npos) return false;
    for (char c : {'|', '&', ';', '`', '$', '>', '<'}) {
        if (path.find(c) != std::string::npos) return false;
    }
    return true;
}

TEST(ConfigPathValidation, NormalPathIsValid) {
    EXPECT_TRUE(ValidatePath("C:\\Users\\Test\\Documents\\NEVEN\\functions"));
    EXPECT_TRUE(ValidatePath("%USERPROFILE%\\Documents\\NEVEN"));
}

TEST(ConfigPathValidation, EmptyPathIsValid) {
    EXPECT_TRUE(ValidatePath(""));
}

TEST(ConfigPathValidation, PathTraversalBlocked) {
    EXPECT_FALSE(ValidatePath("C:\\Users\\..\\Windows\\System32"));
    EXPECT_FALSE(ValidatePath("..\\..\\etc\\passwd"));
}

TEST(ConfigPathValidation, CommandInjectionBlocked) {
    EXPECT_FALSE(ValidatePath("C:\\Users\\test | del *.*"));
    EXPECT_FALSE(ValidatePath("C:\\Users\\test & format C:"));
    EXPECT_FALSE(ValidatePath("C:\\Users\\test; rm -rf /"));
    EXPECT_FALSE(ValidatePath("C:\\Users\\`whoami`"));
    EXPECT_FALSE(ValidatePath("C:\\Users\\$(evil)"));
    EXPECT_FALSE(ValidatePath("C:\\Users\\test > output.txt"));
    EXPECT_FALSE(ValidatePath("C:\\Users\\test < input.txt"));
}
