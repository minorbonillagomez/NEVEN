/**
 * Copyright (c) 2026 NEVEN Project
 *
 * Repository hygiene tests — verify CI configuration, .gitignore patterns,
 * and dead code removal at the repository level.
 */

#include <gtest/gtest.h>
#include <filesystem>
#include <fstream>
#include <string>
#include <vector>

// CMAKE_SOURCE_DIR is passed as a compile definition from CMake
#ifndef CMAKE_SOURCE_DIR
#error "CMAKE_SOURCE_DIR must be defined via CMake"
#endif

namespace fs = std::filesystem;

class RepoHygieneTests : public ::testing::Test {
protected:
    /**
     * @brief Reads an entire file into a string.
     * @param relative_path Path relative to the project source directory.
     * @return File contents as a string, or empty string if file cannot be opened.
     */
    std::string ReadProjectFile(const std::string& relative_path) {
        std::string full_path = std::string(CMAKE_SOURCE_DIR) + "/" + relative_path;
        std::ifstream file(full_path);
        if (!file.is_open()) {
            return "";
        }
        std::string content((std::istreambuf_iterator<char>(file)),
                            std::istreambuf_iterator<char>());
        return content;
    }

    /**
     * @brief Extracts the value of "enabled" inside an engine block of
     *        neven-config.template.json.
     * @param content Template contents.
     * @param engine Engine name as written in the template ("R", "Julia", "Python").
     * @return "true", "false", or an empty string if the key is absent.
     *
     * The engine blocks are flat objects, so the block ends at the first '}'.
     */
    std::string EngineEnabledValue(const std::string& content,
                                   const std::string& engine) {
        std::string key = "\"" + engine + "\": {";
        size_t start = content.find(key);
        if (start == std::string::npos) return "";
        size_t end = content.find('}', start);
        if (end == std::string::npos) return "";
        std::string block = content.substr(start, end - start);
        size_t enabled = block.find("\"enabled\"");
        if (enabled == std::string::npos) return "";

        // The value is read right after the colon of this key, not anywhere in
        // the rest of the block: a later boolean key must not be able to make a
        // "false" read as "true" and hide the regression this test watches.
        size_t colon = block.find(':', enabled);
        if (colon == std::string::npos) return "";
        size_t value = block.find_first_not_of(" \t\r\n", colon + 1);
        if (value == std::string::npos) return "";
        if (block.compare(value, 4, "true") == 0) return "true";
        if (block.compare(value, 5, "false") == 0) return "false";
        return "";
    }

    /**
     * @brief Reads .gitignore and returns all lines.
     */
    std::vector<std::string> ReadGitignoreLines() {
        std::vector<std::string> lines;
        std::string full_path = std::string(CMAKE_SOURCE_DIR) + "/.gitignore";
        std::ifstream file(full_path);
        if (!file.is_open()) {
            return lines;
        }
        std::string line;
        while (std::getline(file, line)) {
            lines.push_back(line);
        }
        return lines;
    }

    /**
     * @brief Checks if a pattern exists as a standalone line in .gitignore.
     *
     * Trims leading/trailing whitespace from each line before comparison.
     */
    bool GitignoreHasPattern(const std::vector<std::string>& lines,
                             const std::string& pattern) {
        for (const auto& line : lines) {
            std::string trimmed = line;
            // Trim leading whitespace
            size_t start = trimmed.find_first_not_of(" \t\r\n");
            if (start == std::string::npos) continue;
            trimmed = trimmed.substr(start);
            // Trim trailing whitespace
            size_t end = trimmed.find_last_not_of(" \t\r\n");
            if (end != std::string::npos) {
                trimmed = trimmed.substr(0, end + 1);
            }
            if (trimmed == pattern) {
                return true;
            }
        }
        return false;
    }
};

// --- CI Permissions Tests (Requirement 6.1) ---

// The workflow lives in .github/ at the repository root, one level above
// CMAKE_SOURCE_DIR (src/), because GitHub only reads .github/ from the root.
TEST_F(RepoHygieneTests, CIWorkflowHasPermissionsBlock) {
    std::string content = ReadProjectFile("../.github/workflows/build-and-test.yml");
    ASSERT_FALSE(content.empty())
        << "Could not read .github/workflows/build-and-test.yml";

    // Verify the workflow declares a permissions block
    EXPECT_NE(content.find("permissions:"), std::string::npos)
        << "build-and-test.yml must declare a 'permissions:' block";
}

TEST_F(RepoHygieneTests, CIWorkflowHasContentsReadPermission) {
    std::string content = ReadProjectFile("../.github/workflows/build-and-test.yml");
    ASSERT_FALSE(content.empty())
        << "Could not read .github/workflows/build-and-test.yml";

    // Verify the workflow restricts to contents: read
    EXPECT_NE(content.find("contents: read"), std::string::npos)
        << "build-and-test.yml must declare 'contents: read' permission";
}

// --- .gitignore Pattern Tests (Requirements 5.1–5.6) ---

TEST_F(RepoHygieneTests, GitignoreExcludesBuildDirectory) {
    auto lines = ReadGitignoreLines();
    ASSERT_FALSE(lines.empty())
        << "Could not read .gitignore file";
    EXPECT_TRUE(GitignoreHasPattern(lines, "Build/"))
        << ".gitignore must exclude Build/ directory (Req 5.1)";
}

TEST_F(RepoHygieneTests, GitignoreExcludesNodeModules) {
    auto lines = ReadGitignoreLines();
    ASSERT_FALSE(lines.empty())
        << "Could not read .gitignore file";
    EXPECT_TRUE(GitignoreHasPattern(lines, "node_modules/"))
        << ".gitignore must exclude node_modules/ directory (Req 5.2)";
}

TEST_F(RepoHygieneTests, GitignoreExcludesPdbFiles) {
    auto lines = ReadGitignoreLines();
    ASSERT_FALSE(lines.empty())
        << "Could not read .gitignore file";
    EXPECT_TRUE(GitignoreHasPattern(lines, "*.pdb"))
        << ".gitignore must exclude *.pdb debug symbol files (Req 5.3)";
}

TEST_F(RepoHygieneTests, GitignoreExcludesPycache) {
    auto lines = ReadGitignoreLines();
    ASSERT_FALSE(lines.empty())
        << "Could not read .gitignore file";
    EXPECT_TRUE(GitignoreHasPattern(lines, "__pycache__/"))
        << ".gitignore must exclude __pycache__/ directory (Req 5.4)";
}

TEST_F(RepoHygieneTests, GitignoreExcludesNevenConfig) {
    auto lines = ReadGitignoreLines();
    ASSERT_FALSE(lines.empty())
        << "Could not read .gitignore file";
    EXPECT_TRUE(GitignoreHasPattern(lines, "neven-config.json"))
        << ".gitignore must exclude neven-config.json to prevent API key leaks (Req 5.5)";
}

TEST_F(RepoHygieneTests, GitignoreExcludesEnvFiles) {
    auto lines = ReadGitignoreLines();
    ASSERT_FALSE(lines.empty())
        << "Could not read .gitignore file";
    EXPECT_TRUE(GitignoreHasPattern(lines, "*.env"))
        << ".gitignore must exclude *.env environment files (Req 5.6)";
}

TEST_F(RepoHygieneTests, GitignoreExcludesKeyFiles) {
    auto lines = ReadGitignoreLines();
    ASSERT_FALSE(lines.empty())
        << "Could not read .gitignore file";
    EXPECT_TRUE(GitignoreHasPattern(lines, "*.key"))
        << ".gitignore must exclude *.key private key files (Req 5.6)";
}

TEST_F(RepoHygieneTests, GitignoreExcludesPemFiles) {
    auto lines = ReadGitignoreLines();
    ASSERT_FALSE(lines.empty())
        << "Could not read .gitignore file";
    EXPECT_TRUE(GitignoreHasPattern(lines, "*.pem"))
        << ".gitignore must exclude *.pem certificate/key files (Req 5.6)";
}

TEST_F(RepoHygieneTests, GitignoreExcludesCrashesDirectory) {
    auto lines = ReadGitignoreLines();
    ASSERT_FALSE(lines.empty())
        << "Could not read .gitignore file";
    EXPECT_TRUE(GitignoreHasPattern(lines, "crashes/"))
        << ".gitignore must exclude crashes/ directory (Req 5.6)";
}

// --- Dead Code Removal Tests (Requirements 13.1, 13.2, 13.3) ---

TEST_F(RepoHygieneTests, DeadCode_JuliaInterface07_DoesNotExist) {
    // Requirement 13.1: language_interface_julia-0.7.ts must not exist
    fs::path julia_07 = fs::path(CMAKE_SOURCE_DIR) /
        "Console" / "src" / "shell" / "language_interface_julia-0.7.ts";
    EXPECT_FALSE(fs::exists(julia_07))
        << "Dead code file Console/src/shell/language_interface_julia-0.7.ts "
           "must be removed (Req 13.1)";
}

TEST_F(RepoHygieneTests, DeadCode_PycacheDirectory_DoesNotExist) {
    // Requirement 13.2: startup/__pycache__/ must not exist
    fs::path pycache = fs::path(CMAKE_SOURCE_DIR) / "startup" / "__pycache__";
    EXPECT_FALSE(fs::exists(pycache))
        << "Dead code directory startup/__pycache__/ must be removed (Req 13.2)";
}

TEST_F(RepoHygieneTests, DeadCode_NevenWebviewDir_DefinedOnce) {
    // Requirement 13.3: .neven_webview_dir() must be defined in exactly one .R file
    fs::path r_dir = fs::path(CMAKE_SOURCE_DIR) / "libreria" / "R";
    ASSERT_TRUE(fs::exists(r_dir) && fs::is_directory(r_dir))
        << "libreria/R/ directory must exist";

    int definition_count = 0;
    std::string defining_file;
    const std::string pattern = ".neven_webview_dir <- function";

    for (const auto& entry : fs::directory_iterator(r_dir)) {
        if (!entry.is_regular_file()) continue;
        if (entry.path().extension() != ".R") continue;

        std::ifstream file(entry.path());
        if (!file.is_open()) continue;

        std::string line;
        while (std::getline(file, line)) {
            if (line.find(pattern) != std::string::npos) {
                definition_count++;
                defining_file = entry.path().filename().string();
                break;  // Only count once per file
            }
        }
    }

    EXPECT_EQ(definition_count, 1)
        << ".neven_webview_dir() must be defined in exactly one .R file (Req 13.3). "
        << "Found " << definition_count << " definitions. "
        << (definition_count > 0 ? "Last found in: " + defining_file : "Not found in any file.");
}

// --- Config and packaging contract tests (INV-BLD-04, INV-INS-01) ---

TEST_F(RepoHygieneTests, ConfigTemplateDeclaresEnabledForTheThreeEngines) {
    std::string content = ReadProjectFile("Install/neven-config.template.json");
    ASSERT_FALSE(content.empty())
        << "Could not read Install/neven-config.template.json";

    // The three engines must declare 'enabled' with the P4 motores_default values:
    // R enabled, Julia and Python left to the user.
    EXPECT_EQ(EngineEnabledValue(content, "R"), "true")
        << "NEVEN.R must declare \"enabled\": true in the config template";
    EXPECT_EQ(EngineEnabledValue(content, "Julia"), "false")
        << "NEVEN.Julia must declare \"enabled\": false in the config template";
    EXPECT_EQ(EngineEnabledValue(content, "Python"), "false")
        << "NEVEN.Python must declare \"enabled\": false in the config template";
}

TEST_F(RepoHygieneTests, RealConfigIsNotInTheRepository) {
    // INV-INS-01: only the template is versioned; a real neven-config.json may
    // carry user credentials and must never reach the repository.
    fs::path real_config = fs::path(CMAKE_SOURCE_DIR) / "Install" / "neven-config.json";
    EXPECT_FALSE(fs::exists(real_config))
        << "Install/neven-config.json must not exist in the repository; "
           "only Install/neven-config.template.json is versioned (INV-INS-01)";
}

TEST_F(RepoHygieneTests, AddinPackagesTheConfigTemplate) {
    std::string content = ReadProjectFile("Addin/CMakeLists.txt");
    ASSERT_FALSE(content.empty())
        << "Could not read Addin/CMakeLists.txt";

    // INV-BLD-04: packaging must take the template, never the (absent) real config.
    EXPECT_EQ(content.find("Install/neven-config.json"), std::string::npos)
        << "Addin/CMakeLists.txt must not reference the inexistent "
           "Install/neven-config.json (INV-BLD-04)";
    EXPECT_NE(content.find("Install/neven-config.template.json"), std::string::npos)
        << "Addin/CMakeLists.txt must copy Install/neven-config.template.json "
           "to Dist/neven-config.json (INV-BLD-04)";
}
