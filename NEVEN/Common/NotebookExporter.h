/**
 * Copyright (c) 2026 RJ2XCL Project — GPL v3
 *
 * @file NotebookExporter.h
 * @brief Captures analysis context and exports as Pluto.jl notebooks.
 */

#pragma once

#include <string>
#include <mutex>
#include <windows.h>

namespace rj2xcl {

/**
 * @brief Exports executed analyses as reproducible Pluto.jl notebooks.
 */
class NotebookExporter {
public:
    /** @brief Context of an executed analysis. */
    struct AnalysisContext {
        std::string function_name;
        std::string language;       // "Julia" or "R"
        std::string code;
        std::string input_data_json;
        std::string parameters_json;
        std::string result_json;
        FILETIME executed_at;
    };

    /** @brief Capture the last analysis for potential export. */
    static void CaptureAnalysis(const AnalysisContext& context);

    /** @brief Returns true if an analysis has been captured in this session. */
    static bool HasAnalysis();

    /**
     * @brief Export the last analysis as a Pluto notebook.
     * @param title Notebook title.
     * @return Absolute file path of the generated .jl file, or error string.
     */
    static std::string ExportNotebook(const std::string& title);

    /** @brief Sanitize a title for use in filenames. */
    static std::string SanitizeTitle(const std::string& title);

    /** @brief Generate a filename from a title with timestamp. */
    static std::string GenerateFilename(const std::string& title);

private:
    static AnalysisContext last_analysis_;
    static std::mutex analysis_mutex_;
    static bool has_analysis_;

    static std::string GeneratePlutoNotebook(const std::string& title,
                                              const AnalysisContext& context);
    static std::string GenerateUUID();
};

} // namespace rj2xcl
