/**
 * Copyright (c) 2026 NEVEN Project
 *
 * R library tests — verify security properties of the R library files
 * in libreria/R/, including elimination of eval(parse()) patterns.
 */

#include <gtest/gtest.h>
#include <filesystem>
#include <fstream>
#include <string>
#include <vector>

namespace fs = std::filesystem;

// CMAKE_SOURCE_DIR is passed as a compile definition from CMake
#ifndef CMAKE_SOURCE_DIR
#error "CMAKE_SOURCE_DIR must be defined via CMake"
#endif

class RLibraryTests : public ::testing::Test {
protected:
    /**
     * @brief Returns the path to the libreria/R/ directory.
     */
    fs::path GetRLibraryPath() {
        return fs::path(CMAKE_SOURCE_DIR) / "libreria" / "R";
    }

    /**
     * @brief Collects all .R files in the libreria/R/ directory.
     * @return Vector of paths to .R files.
     */
    std::vector<fs::path> GetAllRFiles() {
        std::vector<fs::path> r_files;
        fs::path r_dir = GetRLibraryPath();
        if (!fs::exists(r_dir) || !fs::is_directory(r_dir)) {
            return r_files;
        }
        for (const auto& entry : fs::directory_iterator(r_dir)) {
            if (entry.is_regular_file() &&
                entry.path().extension() == ".R") {
                r_files.push_back(entry.path());
            }
        }
        return r_files;
    }

    /**
     * @brief Checks if a file contains the given pattern.
     * @param file_path Path to the file to scan.
     * @param pattern The text pattern to search for.
     * @return true if the pattern is found in the file.
     */
    bool FileContainsPattern(const fs::path& file_path,
                             const std::string& pattern) {
        std::ifstream file(file_path);
        if (!file.is_open()) {
            return false;
        }
        std::string line;
        while (std::getline(file, line)) {
            if (line.find(pattern) != std::string::npos) {
                return true;
            }
        }
        return false;
    }
};

// --- eval(parse()) Elimination Tests (Requirement 9.2) ---

TEST_F(RLibraryTests, NoEvalParseInRLibraryFiles) {
    auto r_files = GetAllRFiles();
    ASSERT_FALSE(r_files.empty())
        << "No .R files found in libreria/R/ directory: "
        << GetRLibraryPath().string();

    std::vector<std::string> files_with_eval_parse;

    for (const auto& file_path : r_files) {
        if (FileContainsPattern(file_path, "eval(parse")) {
            files_with_eval_parse.push_back(file_path.filename().string());
        }
    }

    EXPECT_EQ(files_with_eval_parse.size(), 0u)
        << "Found eval(parse()) in " << files_with_eval_parse.size()
        << " R file(s). All eval(parse()) calls must be replaced with "
        << "as.formula() per Requirement 9.2. Files: "
        << [&]() {
               std::string result;
               for (size_t i = 0; i < files_with_eval_parse.size(); ++i) {
                   if (i > 0) result += ", ";
                   result += files_with_eval_parse[i];
               }
               return result;
           }();
}
