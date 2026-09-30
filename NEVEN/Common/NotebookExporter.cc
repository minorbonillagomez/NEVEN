/**
 * Copyright (c) 2026 RJ2XCL Project — GPL v3
 *
 * @file NotebookExporter.cc
 * @brief Implementation of analysis-to-notebook export.
 */

#include "NotebookExporter.h"
#include "NotebookLibrary.h"
#include "LogService.h"

#include <fstream>
#include <sstream>
#include <algorithm>
#include <random>
#include <iomanip>
#include <ctime>

namespace rj2xcl {

// ─── Static Members ─────────────────────────────────────────────────────

NotebookExporter::AnalysisContext NotebookExporter::last_analysis_;
std::mutex NotebookExporter::analysis_mutex_;
bool NotebookExporter::has_analysis_ = false;

// ─── Capture ────────────────────────────────────────────────────────────

void NotebookExporter::CaptureAnalysis(const AnalysisContext& context) {
    std::lock_guard<std::mutex> lock(analysis_mutex_);
    last_analysis_ = context;
    has_analysis_ = true;
    RJ2XCL_LOG_DEBUG("Analysis captured: %s (%s)", context.function_name.c_str(), context.language.c_str());
}

bool NotebookExporter::HasAnalysis() {
    std::lock_guard<std::mutex> lock(analysis_mutex_);
    return has_analysis_;
}

// ─── Export ─────────────────────────────────────────────────────────────

std::string NotebookExporter::ExportNotebook(const std::string& title) {
    std::lock_guard<std::mutex> lock(analysis_mutex_);

    if (!has_analysis_) {
        RJ2XCL_LOG_WARN("NotebookExporter: no analysis to export");
        return "No analysis to export — execute an analysis first";
    }

    // Generate notebook content
    std::string notebook_content = GeneratePlutoNotebook(title, last_analysis_);

    // Determine output path
    NotebookLibrary lib;
    std::string exports_dir = lib.GetExportsDirectory();

    // Ensure exports directory exists
    CreateDirectoryA(exports_dir.c_str(), nullptr);

    std::string filename = GenerateFilename(title);
    std::string full_path = exports_dir + filename;

    // Write file
    std::ofstream file(full_path, std::ios::binary);
    if (!file.is_open()) {
        RJ2XCL_LOG_ERR("NotebookExporter: cannot write to %s", full_path.c_str());
        return "Error: cannot write notebook file";
    }

    file << notebook_content;
    file.close();

    RJ2XCL_LOG_INFO("Notebook exported: %s", full_path.c_str());
    return full_path;
}

// ─── Filename Generation ────────────────────────────────────────────────

std::string NotebookExporter::SanitizeTitle(const std::string& title) {
    if (title.empty()) return "untitled";

    std::string sanitized;
    sanitized.reserve(title.size());
    for (char c : title) {
        if (std::isalnum(static_cast<unsigned char>(c))) {
            sanitized += c;
        } else {
            sanitized += '_';
        }
    }

    // Collapse multiple underscores
    std::string result;
    bool last_was_underscore = false;
    for (char c : sanitized) {
        if (c == '_') {
            if (!last_was_underscore) result += c;
            last_was_underscore = true;
        } else {
            result += c;
            last_was_underscore = false;
        }
    }

    // Trim trailing underscores
    while (!result.empty() && result.back() == '_') result.pop_back();
    if (result.empty()) return "untitled";

    return result;
}

std::string NotebookExporter::GenerateFilename(const std::string& title) {
    std::string sanitized = SanitizeTitle(title);

    // Timestamp
    time_t now = time(nullptr);
    struct tm tm_buf;
    localtime_s(&tm_buf, &now);

    char timestamp[20];
    strftime(timestamp, sizeof(timestamp), "%Y%m%d_%H%M%S", &tm_buf);

    return sanitized + "_" + timestamp + ".jl";
}

// ─── Pluto Notebook Generation ──────────────────────────────────────────

std::string NotebookExporter::GenerateUUID() {
    static std::mt19937 rng(std::random_device{}());
    std::uniform_int_distribution<uint32_t> dist(0, 0xFFFFFFFF);

    char buf[40];
    snprintf(buf, sizeof(buf), "%08x-%04x-%04x-%04x-%08x%04x",
             dist(rng), dist(rng) & 0xFFFF, (dist(rng) & 0x0FFF) | 0x4000,
             (dist(rng) & 0x3FFF) | 0x8000, dist(rng), dist(rng) & 0xFFFF);
    return std::string(buf);
}

std::string NotebookExporter::GeneratePlutoNotebook(
    const std::string& title,
    const AnalysisContext& context)
{
    std::stringstream ss;

    // Pluto header
    ss << "### A Pluto.jl notebook ###\n";
    ss << "# v0.19.40\n\n";

    // Title cell
    ss << "# \xe2\x95\x94\xe2\x95\x90\xe2\x95\xa1 " << GenerateUUID() << "\n";
    ss << "md\"\"\"\n";
    ss << "# " << (title.empty() ? "Exported Analysis" : title) << "\n";
    ss << "Exported from RJ2XCL — " << context.language << " analysis\n";
    ss << "\"\"\"\n\n";

    // Data cell
    if (!context.input_data_json.empty()) {
        ss << "# \xe2\x95\x94\xe2\x95\x90\xe2\x95\xa1 " << GenerateUUID() << "\n";
        ss << "# Input data\n";
        ss << "input_data_json = \"\"\"" << context.input_data_json << "\"\"\"\n\n";
    }

    // Parameters cell
    if (!context.parameters_json.empty()) {
        ss << "# \xe2\x95\x94\xe2\x95\x90\xe2\x95\xa1 " << GenerateUUID() << "\n";
        ss << "# Parameters\n";
        ss << "parameters_json = \"\"\"" << context.parameters_json << "\"\"\"\n\n";
    }

    // Code cell
    if (!context.code.empty()) {
        ss << "# \xe2\x95\x94\xe2\x95\x90\xe2\x95\xa1 " << GenerateUUID() << "\n";
        ss << "# Analysis code (" << context.function_name << ")\n";
        ss << context.code << "\n\n";
    }

    // Results cell
    if (!context.result_json.empty()) {
        ss << "# \xe2\x95\x94\xe2\x95\x90\xe2\x95\xa1 " << GenerateUUID() << "\n";
        ss << "# Expected results (for verification)\n";
        ss << "expected_result_json = \"\"\"" << context.result_json << "\"\"\"\n\n";
    }

    // Cell order (Pluto requires this at the end)
    ss << "# \xe2\x95\x94\xe2\x95\x90\xe2\x95\xa1 Cell order:\n";

    return ss.str();
}

} // namespace rj2xcl
