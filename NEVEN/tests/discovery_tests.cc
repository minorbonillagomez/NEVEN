/**
 * Copyright (c) 2026 NEVEN Project
 * 
 * Unit tests for DiscoveryService.
 */

#include <gtest/gtest.h>
#include "DiscoveryService.h"
#include <windows.h>
#include <fstream>

namespace rj2xcl {

TEST(DiscoveryServiceTest, Singleton) {
    auto& instance1 = DiscoveryService::Instance();
    auto& instance2 = DiscoveryService::Instance();
    EXPECT_EQ(&instance1, &instance2);
}

TEST(DiscoveryServiceTest, FindRDoesNotCrash) {
    auto results = DiscoveryService::Instance().FindR();
    // We don't know if R is installed, but the function should succeed
}

TEST(DiscoveryServiceTest, FindJuliaDoesNotCrash) {
    auto results = DiscoveryService::Instance().FindJulia();
}

TEST(DiscoveryServiceTest, GetBestVersionOverrides) {
    auto& discovery = DiscoveryService::Instance();
    
    // Test manual home override
    auto best = discovery.GetBestVersion("R", "", "C:\\Manual\\R");
    EXPECT_EQ(best.home_path, "C:\\Manual\\R");
    EXPECT_EQ(best.version, "Override");

    // Test tag matching (if any versions found)
    auto installs = discovery.FindR();
    if (!installs.empty()) {
        std::string first_ver = installs[0].version;
        auto matched = discovery.GetBestVersion("R", first_ver, "");
        EXPECT_FALSE(matched.home_path.empty());
        EXPECT_EQ(matched.version, first_ver);
    }
}

} // namespace rj2xcl
