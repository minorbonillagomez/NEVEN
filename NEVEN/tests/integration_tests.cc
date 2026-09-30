#include <gtest/gtest.h>
#include <gmock/gmock.h>
#include <windows.h>
#include <iostream>
#include <filesystem>
#include <fstream>
#include <string>
#include <vector>
#include "language_service.h"
#include "callback_info.h"
#include "com_object_map.h"
#include "json11/json11.hpp"

// CMAKE_SOURCE_DIR is passed as a compile definition from CMake
#ifndef CMAKE_SOURCE_DIR
#error "CMAKE_SOURCE_DIR must be defined via CMake"
#endif

namespace fs = std::filesystem;

using namespace rj2xcl;

class IPCIntegrationTest : public ::testing::Test {
protected:
    CallbackInfo cb_info_;
    COMObjectMap map_;
    std::shared_ptr<LanguageService> svc_;
    
    void SetUp() override {
        // Setup configuration that points child_path to the built mock_engine_backend
        auto err = std::string();
        auto config = json11::Json::parse(
            R"({ "name": "MockEngine", "prefix": "MOCK", "executable": "mock_engine_backend.exe", "named_arguments": false })",
            err);
        
        // Configure path to point strictly where the test executable is located.
        char path_buf[MAX_PATH];
        GetModuleFileNameA(NULL, path_buf, MAX_PATH);
        std::filesystem::path exe_path(path_buf);
        std::string home_dir = exe_path.parent_path().string();

        // We must provide a valid system-level config so LanguageService marks as configured_ = true
        // and uses the override_home to skip DiscoveryService logic for "MockEngine"
        auto system_config = json11::Json::object{
            {"NEVEN", json11::Json::object{
                {"MockEngine", json11::Json::object{
                    {"home", home_dir}
                }}
            }}
        };

        svc_ = std::make_shared<LanguageService>(cb_info_, map_, 0, system_config, home_dir, config);
    }
    
    void TearDown() override {
        if (svc_) {
            svc_->Shutdown();
            svc_.reset();
        }
    }
};

TEST_F(IPCIntegrationTest, FullNamedPipeLifecycle_ConnectsAndSendsProtobuf) {
    // 1. Launch Process and Connect
    HANDLE job_handle = CreateJobObject(NULL, NULL);
    ASSERT_NE(job_handle, nullptr);

    std::cout << "Starting connection logic... target is: " << svc_->name() << std::endl;
    // Note: Do NOT call StartChildProcess manually, Connect() does it.
    svc_->Connect(job_handle);
    ASSERT_TRUE(svc_->connected()) << "LanguageService failed to connect! Check if mock_engine_backend.exe path is correct.";
    ASSERT_TRUE(svc_->connected());

    // 2. Perform a sample RPC call (Code execution)
    RJ2XCLBuffers::CallResponse req, resp;
    req.mutable_code()->add_line("print('hello')");
    req.set_wait(true); // Must tell LanguageService to wait for response

    // The LanguageService::Call assigns IDs, frames it, sends it
    svc_->Call(resp, req);
    
    EXPECT_TRUE(resp.has_result());
    EXPECT_EQ(resp.result().str(), "MOCK_OK");

    // Cleanup handles
    CloseHandle(job_handle);
}


// --- Console Independence Tests (Requirement 2.1) ---

/**
 * @brief Tests that Core/ and Common/ have no compile-time dependency on Console/.
 *
 * Validates Requirement 2.1: NEVEN_Core SHALL function completely without
 * the Console module present in the file system.
 */
class ConsoleIndependenceTests : public ::testing::Test {
protected:
    /**
     * @brief Recursively collects all .cc and .h files in a directory.
     */
    std::vector<fs::path> CollectSourceFiles(const fs::path& dir) {
        std::vector<fs::path> files;
        if (!fs::exists(dir) || !fs::is_directory(dir)) {
            return files;
        }
        for (const auto& entry : fs::recursive_directory_iterator(dir)) {
            if (!entry.is_regular_file()) continue;
            auto ext = entry.path().extension().string();
            if (ext == ".cc" || ext == ".h" || ext == ".cpp" || ext == ".hpp") {
                files.push_back(entry.path());
            }
        }
        return files;
    }

    /**
     * @brief Scans a source file for #include lines referencing Console/ paths.
     * @return Vector of (line_number, line_content) pairs for matches found.
     */
    std::vector<std::pair<int, std::string>> FindConsoleIncludes(const fs::path& file) {
        std::vector<std::pair<int, std::string>> matches;
        std::ifstream ifs(file);
        if (!ifs.is_open()) return matches;

        std::string line;
        int line_number = 0;
        while (std::getline(ifs, line)) {
            line_number++;
            // Look for #include directives that reference Console/
            if (line.find("#include") != std::string::npos &&
                line.find("Console/") != std::string::npos) {
                matches.push_back({line_number, line});
            }
        }
        return matches;
    }
};

TEST_F(ConsoleIndependenceTests, CoreHasNoConsoleIncludes) {
    // Scan all source files in Core/ for #include referencing Console/
    fs::path core_dir = fs::path(CMAKE_SOURCE_DIR) / "Core";
    ASSERT_TRUE(fs::exists(core_dir))
        << "Core/ directory must exist at " << core_dir.string();

    auto source_files = CollectSourceFiles(core_dir);
    ASSERT_FALSE(source_files.empty())
        << "Core/ directory should contain source files";

    std::vector<std::string> violations;
    for (const auto& file : source_files) {
        auto matches = FindConsoleIncludes(file);
        for (const auto& [line_num, line_content] : matches) {
            violations.push_back(
                file.filename().string() + ":" + std::to_string(line_num) +
                " -> " + line_content);
        }
    }

    EXPECT_EQ(violations.size(), 0u)
        << "Core/ source files must not #include Console/ paths (Req 2.1). "
        << "Found " << violations.size() << " violation(s):\n"
        << [&]() {
               std::string msg;
               for (const auto& v : violations) msg += "  " + v + "\n";
               return msg;
           }();
}

TEST_F(ConsoleIndependenceTests, CommonHasNoConsoleIncludes) {
    // Scan all source files in Common/ for #include referencing Console/
    fs::path common_dir = fs::path(CMAKE_SOURCE_DIR) / "Common";
    ASSERT_TRUE(fs::exists(common_dir))
        << "Common/ directory must exist at " << common_dir.string();

    auto source_files = CollectSourceFiles(common_dir);
    ASSERT_FALSE(source_files.empty())
        << "Common/ directory should contain source files";

    std::vector<std::string> violations;
    for (const auto& file : source_files) {
        auto matches = FindConsoleIncludes(file);
        for (const auto& [line_num, line_content] : matches) {
            violations.push_back(
                file.filename().string() + ":" + std::to_string(line_num) +
                " -> " + line_content);
        }
    }

    EXPECT_EQ(violations.size(), 0u)
        << "Common/ source files must not #include Console/ paths (Req 2.1). "
        << "Found " << violations.size() << " violation(s):\n"
        << [&]() {
               std::string msg;
               for (const auto& v : violations) msg += "  " + v + "\n";
               return msg;
           }();
}

TEST_F(ConsoleIndependenceTests, ConsoleDirectoryDoesNotExist) {
    // Console (Electron REPL) was removed in the security remediation.
    // The WebView2-based REPL (REPLManager + REPLBridge) is the replacement.
    // Verify Console/ directory no longer exists in the source tree.
    fs::path console_dir = fs::path(CMAKE_SOURCE_DIR) / "Console";
    EXPECT_FALSE(fs::exists(console_dir))
        << "Console/ directory must not exist — it was removed and replaced by "
           "the WebView2 REPL (REPLManager + REPLBridge). Req 2.1 satisfied by "
           "complete elimination rather than conditional inclusion.";
}
