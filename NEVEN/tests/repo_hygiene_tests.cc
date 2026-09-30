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

TEST_F(RepoHygieneTests, CIWorkflowHasPermissionsBlock) {
    std::string content = ReadProjectFile(".github/workflows/build-and-test.yml");
    ASSERT_FALSE(content.empty())
        << "Could not read .github/workflows/build-and-test.yml";

    // Verify the workflow declares a permissions block
    EXPECT_NE(content.find("permissions:"), std::string::npos)
        << "build-and-test.yml must declare a 'permissions:' block";
}

TEST_F(RepoHygieneTests, CIWorkflowHasContentsReadPermission) {
    std::string content = ReadProjectFile(".github/workflows/build-and-test.yml");
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
