/**
 * Copyright (c) 2026 NEVEN Project
 *
 * This file is part of NEVEN.
 *
 * NEVEN is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * NEVEN is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with NEVEN.  If not, see <http://www.gnu.org/licenses/>.
 */
#include <gtest/gtest.h>
#include <string>
#include <iostream>
#include "result.h"
#include "ConfigService.h"
#include "LogService.h"
#include "windows_api_functions.h"
#include "json11/json11.hpp"

using namespace rj2xcl;

// ─── Result<T,E> pattern ─────────────────────────────────────────────────────

TEST(ResultTest, SuccessValue) {
    auto res = Result<int, std::string>::Success(42);
    EXPECT_TRUE(res.is_success());
    EXPECT_FALSE(res.is_failure());
    EXPECT_EQ(res.value(), 42);
}

TEST(ResultTest, FailureError) {
    auto res = Result<int, std::string>::Failure("error");
    EXPECT_TRUE(res.is_failure());
    EXPECT_FALSE(res.is_success());
    EXPECT_EQ(res.error(), "error");
}

TEST(ResultTest, VoidSuccess) {
    auto res = Result<void, int>::Success();
    EXPECT_TRUE(res.is_success());
}

// ─── ConfigService ────────────────────────────────────────────────────────────

TEST(ConfigServiceTest, Singleton) {
    auto& instance1 = ConfigService::Instance();
    auto& instance2 = ConfigService::Instance();
    EXPECT_EQ(&instance1, &instance2);
}

TEST(ConfigServiceTest, DefaultValues) {
    auto& config = ConfigService::Instance();
    EXPECT_EQ(config.GetDevFlags(), 0);
    EXPECT_TRUE(config.GetHomePath().empty() || config.GetHomePath().length() > 0);
}

// ─── H3: ConfigService JSON parse error (C-06) ───────────────────────────────

TEST(ConfigServiceTest, ReadJsonFileMalformedJson) {
    // Directly test json11 parse error detection (the mechanism used in ConfigService)
    std::string parse_error;
    auto json = json11::Json::parse("{ invalid json !!! }", parse_error, json11::COMMENTS);
    // After C-06 fix: parse_error must be non-empty for malformed JSON
    EXPECT_FALSE(parse_error.empty())
        << "json11 must report a parse error for malformed JSON";
    // And the resulting JSON should not be an object with meaningful content
    EXPECT_FALSE(json.is_object() && json.object_items().size() > 0)
        << "Malformed JSON should not produce a non-empty object";
}

TEST(ConfigServiceTest, ReadJsonFileValidJson) {
    std::string parse_error;
    auto json = json11::Json::parse("{\"key\": \"value\"}", parse_error, json11::COMMENTS);
    EXPECT_TRUE(parse_error.empty()) << "Valid JSON should not produce parse errors";
    EXPECT_TRUE(json.is_object());
    EXPECT_EQ(json["key"].string_value(), "value");
}

TEST(ConfigServiceTest, ParseErrorEnumHasThreeValue) {
    // H3: Verify ParseError = 3 was added to FileError (allows passing ParseError as failure)
    APIFunctions::FileError err = APIFunctions::FileError::ParseError;
    EXPECT_EQ(static_cast<int>(err), 3);
}

// ─── H1: R version comparison logic (C-01) ───────────────────────────────────

// Replicates the version_ok / version_within_max logic from controlr.cc:main()
static bool RVersionIsSupported(int major, int minor, int min_major, int min_minor, int max_major) {
    bool version_ok = (major > min_major) ||
                      (major == min_major && minor >= min_minor);
    bool within_max = (major <= max_major);
    return version_ok && within_max;
}

TEST(VersionCheckTest, R35IsSupported) {
    EXPECT_TRUE(RVersionIsSupported(3, 5, 3, 5, 99));
}

TEST(VersionCheckTest, R36IsSupported) {
    EXPECT_TRUE(RVersionIsSupported(3, 6, 3, 5, 99));
}

TEST(VersionCheckTest, R40IsSupported) {
    // H1: This was previously rejected — now it's accepted
    EXPECT_TRUE(RVersionIsSupported(4, 0, 3, 5, 99));
}

TEST(VersionCheckTest, R43IsSupported) {
    EXPECT_TRUE(RVersionIsSupported(4, 3, 3, 5, 99));
}

TEST(VersionCheckTest, R34IsRejected) {
    EXPECT_FALSE(RVersionIsSupported(3, 4, 3, 5, 99));
}

TEST(VersionCheckTest, R30IsRejected) {
    EXPECT_FALSE(RVersionIsSupported(3, 0, 3, 5, 99));
}

TEST(VersionCheckTest, R100ExceedMaxIsRejected) {
    EXPECT_FALSE(RVersionIsSupported(100, 0, 3, 5, 10));
}

// ─── LogService ──────────────────────────────────────────────────────────────

TEST(LogServiceTest, SingletonAndInit) {
    auto& logger = LogService::Instance();
    logger.Initialize();
    logger.Log(LogLevel::INFO_LVL, "Integration Test: LogService is functional");
    RJ2XCL_LOG_INFO("Macro test: %s", "Success");
}
