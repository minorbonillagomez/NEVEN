/**
 * @file sensitivity_test.cc
 * @brief Unit tests for SensitivityService — validates parsing and formatting.
 *
 * Copyright (c) 2026 NEVEN Project — GPL v3
 */

#include <gtest/gtest.h>
#include <windows.h>
#undef ERROR
#include "sensitivity_service.h"
#include "json11/json11.hpp"
#include <string>
#include <vector>
#include <cmath>

namespace neven_sim {
namespace testing {

// ─── Parsing Tests ───────────────────────────────────────────────────────────

TEST(SensitivityServiceTest, ParseJSON_ValidArray) {
    std::string json = R"([
        {"name":"Ventas","rho":0.82,"contrib":0.58},
        {"name":"Costos","rho":-0.45,"contrib":0.28},
        {"name":"TipoCambio","rho":0.31,"contrib":0.14}
    ])";

    std::vector<SensitivityEntry> sensitivity;
    ASSERT_TRUE(SensitivityService::ParseSensitivityResults(json, sensitivity));
    ASSERT_EQ(sensitivity.size(), 3u);

    // Should be sorted by |rho| descending
    EXPECT_EQ(sensitivity[0].name, "Ventas");
    EXPECT_DOUBLE_EQ(sensitivity[0].spearman_rho, 0.82);
    EXPECT_DOUBLE_EQ(sensitivity[0].contribution, 0.58);

    EXPECT_EQ(sensitivity[1].name, "Costos");
    EXPECT_DOUBLE_EQ(sensitivity[1].spearman_rho, -0.45);

    EXPECT_EQ(sensitivity[2].name, "TipoCambio");
    EXPECT_DOUBLE_EQ(sensitivity[2].spearman_rho, 0.31);
}

TEST(SensitivityServiceTest, ParseJSON_SingleEntry) {
    std::string json = R"([{"name":"X","rho":0.95,"contrib":1.0}])";

    std::vector<SensitivityEntry> sensitivity;
    ASSERT_TRUE(SensitivityService::ParseSensitivityResults(json, sensitivity));
    ASSERT_EQ(sensitivity.size(), 1u);
    EXPECT_EQ(sensitivity[0].name, "X");
    EXPECT_DOUBLE_EQ(sensitivity[0].contribution, 1.0);
}

TEST(SensitivityServiceTest, ParseJSON_EmptyArray) {
    std::string json = "[]";
    std::vector<SensitivityEntry> sensitivity;
    EXPECT_FALSE(SensitivityService::ParseSensitivityResults(json, sensitivity));
}

TEST(SensitivityServiceTest, ParseJSON_ErrorString) {
    std::string json = "[ERROR] No simulation data available";
    std::vector<SensitivityEntry> sensitivity;
    EXPECT_FALSE(SensitivityService::ParseSensitivityResults(json, sensitivity));
}

TEST(SensitivityServiceTest, ParseJSON_InvalidJSON) {
    std::string json = "this is not json";
    std::vector<SensitivityEntry> sensitivity;
    EXPECT_FALSE(SensitivityService::ParseSensitivityResults(json, sensitivity));
}

TEST(SensitivityServiceTest, ParseJSON_EmptyString) {
    std::vector<SensitivityEntry> sensitivity;
    EXPECT_FALSE(SensitivityService::ParseSensitivityResults("", sensitivity));
}

TEST(SensitivityServiceTest, ParseJSON_SortsByAbsoluteRho) {
    // Input not sorted — should be sorted by |rho|
    std::string json = R"([
        {"name":"A","rho":0.2,"contrib":0.04},
        {"name":"B","rho":-0.9,"contrib":0.81},
        {"name":"C","rho":0.5,"contrib":0.15}
    ])";

    std::vector<SensitivityEntry> sensitivity;
    ASSERT_TRUE(SensitivityService::ParseSensitivityResults(json, sensitivity));

    // Sorted: B (|0.9|), C (|0.5|), A (|0.2|)
    EXPECT_EQ(sensitivity[0].name, "B");
    EXPECT_EQ(sensitivity[1].name, "C");
    EXPECT_EQ(sensitivity[2].name, "A");
}

// ─── Formatting Tests ────────────────────────────────────────────────────────

TEST(SensitivityServiceTest, FormatForExcel_MultipleEntries) {
    std::vector<SensitivityEntry> sensitivity = {
        {"Ventas", 0.82, 0.58},
        {"Costos", -0.45, 0.28},
        {"TipoCambio", 0.31, 0.14}
    };

    std::string result = SensitivityService::FormatForExcel(sensitivity);
    EXPECT_TRUE(result.find("Ventas") != std::string::npos);
    EXPECT_TRUE(result.find("rho=") != std::string::npos);
    EXPECT_TRUE(result.find("0.820") != std::string::npos);
    EXPECT_TRUE(result.find("(58%)") != std::string::npos || result.find("58%") != std::string::npos);
    EXPECT_TRUE(result.find(";") != std::string::npos);
}

TEST(SensitivityServiceTest, FormatForExcel_Empty) {
    std::vector<SensitivityEntry> sensitivity;
    std::string result = SensitivityService::FormatForExcel(sensitivity);
    EXPECT_EQ(result, "Sin datos de sensibilidad");
}

TEST(SensitivityServiceTest, FormatForWebViewer_ValidJSON) {
    std::vector<SensitivityEntry> sensitivity = {
        {"A", 0.9, 0.81},
        {"B", -0.3, 0.09}
    };

    std::string result = SensitivityService::FormatForWebViewer(sensitivity);

    // Verify it's valid JSON
    std::string err;
    json11::Json json = json11::Json::parse(result, err);
    EXPECT_TRUE(err.empty());
    EXPECT_TRUE(json.is_object());
    EXPECT_EQ(json["type"].string_value(), "sensitivity");
    EXPECT_EQ(json["variables"].array_items().size(), 2u);
    EXPECT_EQ(json["spearman"].array_items().size(), 2u);
    EXPECT_EQ(json["contribution"].array_items().size(), 2u);
}

TEST(SensitivityServiceTest, FormatForWebViewer_Empty) {
    std::vector<SensitivityEntry> sensitivity;
    EXPECT_EQ(SensitivityService::FormatForWebViewer(sensitivity), "[]");
}

} // namespace testing
} // namespace neven_sim
