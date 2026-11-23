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

    // A home override that exists as a directory is honoured as-is
    char temp_path[MAX_PATH] = {};
    ASSERT_GT(GetTempPathA(MAX_PATH, temp_path), 0u);
    std::string valid_home = std::string(temp_path) + "neven_discovery_override";
    ASSERT_TRUE(CreateDirectoryA(valid_home.c_str(), nullptr) || GetLastError() == ERROR_ALREADY_EXISTS);

    auto best = discovery.GetBestVersion("R", "", valid_home);
    EXPECT_EQ(best.home_path, valid_home);
    EXPECT_EQ(best.version, "Override");

    RemoveDirectoryA(valid_home.c_str());

    // An override that does not exist must NOT be reported as an installation:
    // a home left over from packaging or from an uninstalled engine would
    // otherwise make an absent engine look present.
    auto stale = discovery.GetBestVersion("R", "", "C:\\Manual\\R");
    EXPECT_NE(stale.home_path, "C:\\Manual\\R");
    EXPECT_NE(stale.version, "Override");

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
