#include <gtest/gtest.h>
#include "StudioEndpoint.h"

using namespace neven;

TEST(StudioEndpoint, UrlUsesHttpsWhenCertificateConfigured) {
    EXPECT_EQ(StudioUrl(true, 5555, "/taskpane.html"), "https://localhost:5555/taskpane.html");
    EXPECT_EQ(StudioUrlW(true, 5555, L"/taskpane.html"), L"https://localhost:5555/taskpane.html");
}

TEST(StudioEndpoint, UrlUsesHttpWithoutCertificate) {
    EXPECT_EQ(StudioUrl(false, 5555, "/taskpane.html"), "http://localhost:5555/taskpane.html");
    EXPECT_EQ(StudioBaseUrl(false, 5556), "http://localhost:5556");
}

TEST(StudioEndpoint, WinHttpFlagFollowsScheme) {
    EXPECT_EQ(StudioOpenFlags(true), (DWORD)WINHTTP_FLAG_SECURE);
    EXPECT_EQ(StudioOpenFlags(false), (DWORD)0);
}

TEST(StudioEndpoint, HttpsOnlyWhenBothPathsSetAndFilesExist) {
    EXPECT_TRUE(StudioHttpsFromPaths("a.crt", "a.key", true, true));
    EXPECT_FALSE(StudioHttpsFromPaths("", "", true, true));
    EXPECT_FALSE(StudioHttpsFromPaths("a.crt", "", true, true));
    EXPECT_FALSE(StudioHttpsFromPaths("a.crt", "a.key", true, false));
    EXPECT_FALSE(StudioHttpsFromPaths("a.crt", "a.key", false, true));
}

TEST(StudioEndpoint, CertPathsAreReadFromTaskPaneSection) {
    const std::string cfg =
        "{ \"Pluto\": {\"port\": 1234},\n"
        "  \"TaskPane\": {\n"
        "    \"port\": 5555,\n"
        "    \"certPath\": \"C:\\\\NEVEN\\\\certs\\\\localhost.crt\",\n"
        "    \"keyPath\": \"C:\\\\NEVEN\\\\certs\\\\localhost.key\" } }";
    std::string cert, key;
    StudioCertPathsFromConfig(cfg, cert, key);
    EXPECT_EQ(cert, "C:\\NEVEN\\certs\\localhost.crt");
    EXPECT_EQ(key, "C:\\NEVEN\\certs\\localhost.key");
}

TEST(StudioEndpoint, EmptyOrMissingCertPathsMeanHttp) {
    std::string cert = "x", key = "x";
    StudioCertPathsFromConfig("{\"TaskPane\": {\"certPath\": \"\", \"keyPath\": \"\"}}", cert, key);
    EXPECT_TRUE(cert.empty());
    EXPECT_TRUE(key.empty());
    StudioCertPathsFromConfig("{\"Pluto\": {\"port\": 1234}}", cert, key);
    EXPECT_TRUE(cert.empty());
    EXPECT_FALSE(StudioHttpsFromPaths(cert, key, true, true));
}

TEST(StudioEndpoint, NavigationPolicyAcceptsHttpAndHttpsOnTheStudioPort) {
    EXPECT_TRUE(StudioIsLocalUrl(L"http://localhost:5555/taskpane.html", 5555));
    EXPECT_TRUE(StudioIsLocalUrl(L"https://localhost:5555/taskpane.html", 5555));
    EXPECT_TRUE(StudioIsLocalUrl(L"https://127.0.0.1:5555/", 5555));
    EXPECT_FALSE(StudioIsLocalUrl(L"https://localhost:5556/", 5555));
    EXPECT_FALSE(StudioIsLocalUrl(L"https://evil.example/?u=https://localhost:5555", 5555));
}

TEST(StudioEndpoint, ProbeOfClosedPortFindsNoServer) {
    // Port 1 is never served; both schemes must fail quickly and not report alive.
    bool https = true;
    EXPECT_FALSE(StudioIsAlive(1, &https));
}