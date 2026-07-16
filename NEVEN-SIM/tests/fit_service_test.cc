/**
 * @file fit_service_test.cc
 * @brief Unit tests for FitService â€” validates parsing logic without R.
 *
 * Tests the JSON and structured-text parsing of distribution fit results.
 * Does not require R to be running.
 *
 * Copyright (c) 2026 NEVEN Project â€” GPL v3
 */

#include <gtest/gtest.h>
#include <windows.h>
#undef ERROR
#include "fit_service.h"
#include <vector>
#include <string>

namespace neven_sim {
namespace testing {

// â”€â”€â”€ Helper: FitService methods are public (stateless utility class) â”€â”€â”€â”€â”€â”€â”€â”€â”€

using FitServiceTestHelper = FitService;

// â”€â”€â”€ JSON Parsing Tests â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

TEST(FitServiceTest, ParseJSON_ValidSingleDistribution) {
    std::string json = R"({"norm":{"params":{"mean":5.2,"sd":1.3},"aic":2340.5,"ks_stat":0.04,"ad_stat":0.8}})";

    std::vector<FitResult> results;
    ASSERT_TRUE(FitServiceTestHelper::ParseFitResults(json, results));
    ASSERT_EQ(results.size(), 1u);

    EXPECT_EQ(results[0].dist_name, "norm");
    EXPECT_DOUBLE_EQ(results[0].param1, 5.2);
    EXPECT_DOUBLE_EQ(results[0].param2, 1.3);
    EXPECT_DOUBLE_EQ(results[0].aic, 2340.5);
    EXPECT_DOUBLE_EQ(results[0].ks_p, 0.04);
    EXPECT_DOUBLE_EQ(results[0].ad_p, 0.8);
}

TEST(FitServiceTest, ParseJSON_MultipleDistributions) {
    std::string json = R"({
        "norm":{"params":{"mean":5.0,"sd":1.0},"aic":2340,"ks_stat":0.04,"ad_stat":0.8},
        "lnorm":{"params":{"meanlog":1.6,"sdlog":0.3},"aic":2355,"ks_stat":0.06,"ad_stat":1.2},
        "gamma":{"params":{"shape":3.0,"rate":0.6},"aic":2320,"ks_stat":0.03,"ad_stat":0.5}
    })";

    std::vector<FitResult> results;
    ASSERT_TRUE(FitServiceTestHelper::ParseFitResults(json, results));
    ASSERT_EQ(results.size(), 3u);

    // Should be sorted by AIC ascending (gamma=2320, norm=2340, lnorm=2355)
    EXPECT_EQ(results[0].dist_name, "gamma");
    EXPECT_DOUBLE_EQ(results[0].aic, 2320.0);
    EXPECT_EQ(results[1].dist_name, "norm");
    EXPECT_DOUBLE_EQ(results[1].aic, 2340.0);
    EXPECT_EQ(results[2].dist_name, "lnorm");
    EXPECT_DOUBLE_EQ(results[2].aic, 2355.0);
}

TEST(FitServiceTest, ParseJSON_EmptyObject) {
    std::string json = "{}";
    std::vector<FitResult> results;
    EXPECT_FALSE(FitServiceTestHelper::ParseFitResults(json, results));
    EXPECT_TRUE(results.empty());
}

// â”€â”€â”€ Structured Text Parsing Tests â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

TEST(FitServiceTest, ParseText_SingleDistribution) {
    std::string text = "norm|mean=5.2,sd=1.3|2340.5|0.04";

    std::vector<FitResult> results;
    ASSERT_TRUE(FitServiceTestHelper::ParseFitResults(text, results));
    ASSERT_EQ(results.size(), 1u);

    EXPECT_EQ(results[0].dist_name, "norm");
    EXPECT_DOUBLE_EQ(results[0].param1, 5.2);
    EXPECT_DOUBLE_EQ(results[0].param2, 1.3);
    EXPECT_DOUBLE_EQ(results[0].aic, 2340.5);
    EXPECT_DOUBLE_EQ(results[0].ks_p, 0.04);
}

TEST(FitServiceTest, ParseText_MultipleDistributions) {
    std::string text = "norm|mean=5.0,sd=1.0|2340|0.04;;gamma|shape=3.0,rate=0.6|2320|0.03";

    std::vector<FitResult> results;
    ASSERT_TRUE(FitServiceTestHelper::ParseFitResults(text, results));
    ASSERT_EQ(results.size(), 2u);

    // Sorted by AIC: gamma first
    EXPECT_EQ(results[0].dist_name, "gamma");
    EXPECT_DOUBLE_EQ(results[0].aic, 2320.0);
    EXPECT_EQ(results[1].dist_name, "norm");
    EXPECT_DOUBLE_EQ(results[1].aic, 2340.0);
}

TEST(FitServiceTest, ParseText_InvalidInput) {
    std::string text = "[ERROR] fitdistrplus not installed";
    std::vector<FitResult> results;
    // This should fail because there are no valid entries
    EXPECT_FALSE(FitServiceTestHelper::ParseFitResults(text, results));
}

// â”€â”€â”€ Code Generation Tests â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

TEST(FitServiceTest, GenerateCode_ContainsDataVector) {
    std::vector<double> data = {1.5, 2.3, 3.7, 4.1, 5.9};
    std::string code = FitServiceTestHelper::GenerateFitCode(data);

    EXPECT_TRUE(code.find("1.5") != std::string::npos);
    EXPECT_TRUE(code.find("5.9") != std::string::npos);
    EXPECT_TRUE(code.find("fitdistrplus") != std::string::npos);
    EXPECT_TRUE(code.find("fitdist") != std::string::npos);
}

TEST(FitServiceTest, GenerateCode_ContainsCandidates) {
    std::vector<double> data = {1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0};
    std::string code = FitServiceTestHelper::GenerateFitCode(data);

    EXPECT_TRUE(code.find("'norm'") != std::string::npos);
    EXPECT_TRUE(code.find("'lnorm'") != std::string::npos);
    EXPECT_TRUE(code.find("'gamma'") != std::string::npos);
    EXPECT_TRUE(code.find("'weibull'") != std::string::npos);
    EXPECT_TRUE(code.find("'exp'") != std::string::npos);
    EXPECT_TRUE(code.find("'unif'") != std::string::npos);
}

TEST(FitServiceTest, GenerateCode_WrapsInTryCatch) {
    std::vector<double> data = {1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0};
    std::string code = FitServiceTestHelper::GenerateFitCode(data);

    EXPECT_TRUE(code.find("tryCatch") != std::string::npos);
    EXPECT_TRUE(code.find("[ERROR]") != std::string::npos);
}

// â”€â”€â”€ Minimum Data Validation â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

TEST(FitServiceTest, FitDistributions_TooFewDataPoints) {
    std::vector<double> data = {1.0, 2.0, 3.0};  // Less than 10
    std::vector<FitResult> results;
    EXPECT_FALSE(FitService::FitDistributions(data, results));
}

TEST(FitServiceTest, FitDistributions_EmptyData) {
    std::vector<double> data;
    std::vector<FitResult> results;
    EXPECT_FALSE(FitService::FitDistributions(data, results));
}

} // namespace testing
} // namespace neven_sim

