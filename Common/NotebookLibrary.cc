/**
 * Copyright (c) 2026 RJ2XCL Project — GPL v3
 *
 * @file NotebookLibrary.cc
 * @brief Implementation of notebook discovery and management.
 */

#include "NotebookLibrary.h"
#include "ConfigService.h"
#include "LogService.h"

#include <windows.h>
#include <algorithm>
#include <sstream>

namespace rj2xcl {

// ─── Preconfigured Notebook Registry ────────────────────────────────────

const NotebookLibrary::PreconfiguredEntry NotebookLibrary::PRECONFIGURED_NOTEBOOKS[] = {
    // R via RCall.jl (7)
    {"stats_regression.jl",        "R via RCall"},
    {"lme4_mixed_models.jl",       "R via RCall"},
    {"survival_analysis.jl",       "R via RCall"},
    {"forecast_arima.jl",          "R via RCall"},
    {"psych_factor_analysis.jl",   "R via RCall"},
    {"plm_panel_econometrics.jl",  "R via RCall"},
    {"rstanarm_bayes.jl",          "R via RCall"},
    // Julia native (5)
    {"jump_optimization.jl",       "Julia native"},
    {"diffeq_simulation.jl",       "Julia native"},
    {"turing_hierarchical.jl",     "Julia native"},
    {"montecarlo_risk.jl",         "Julia native"},
    {"linalg_decomposition.jl",    "Julia native"},
    // Mixed R+Julia (1)
    {"multilang_pipeline.jl",      "Mixed R+Julia"},
    // Excel integration (2)
    {"excel_dashboard.jl",         "Excel Data"},
    {"excel_data.jl",              "Excel Data"},
    // Aerospace / Scientific Computing (1)
    {"hl20_reentry.jl",            "Aerospace"},
};

const int NotebookLibrary::PRECONFIGURED_COUNT = sizeof(PRECONFIGURED_NOTEBOOKS) / sizeof(PRECONFIGURED_NOTEBOOKS[0]);

// ─── Paths ──────────────────────────────────────────────────────────────

std::string NotebookLibrary::GetNotebooksDirectory() const {
    // Use Documents\NEVEN\notebooks\ (same parent as functions\)
    // Expand %USERPROFILE% manually to avoid dependency on ConfigService initialization order
    char user_profile[MAX_PATH] = {};
    DWORD len = GetEnvironmentVariableA("USERPROFILE", user_profile, MAX_PATH);
    if (len > 0 && len < MAX_PATH) {
        return std::string(user_profile) + "\\Documents\\NEVEN\\notebooks\\";
    }
    // Fallback
    return ConfigService::Instance().GetHomePath() + "notebooks\\";
}

std::string NotebookLibrary::GetCustomDirectory() const {
    return GetNotebooksDirectory() + "custom\\";
}

std::string NotebookLibrary::GetExportsDirectory() const {
    return GetNotebooksDirectory() + "exports\\";
}

// ─── Discovery ──────────────────────────────────────────────────────────

std::vector<NotebookLibrary::NotebookInfo> NotebookLibrary::ListNotebooks() const {
    std::vector<NotebookInfo> result;
    std::string notebooks_dir = GetNotebooksDirectory();
    std::string custom_dir = GetCustomDirectory();

    // Scan preconfigured notebooks
    for (int i = 0; i < PRECONFIGURED_COUNT; i++) {
        std::string full_path = notebooks_dir + PRECONFIGURED_NOTEBOOKS[i].filename;
        DWORD attrs = GetFileAttributesA(full_path.c_str());
        if (attrs != INVALID_FILE_ATTRIBUTES) {
            NotebookInfo info;
            info.filename = PRECONFIGURED_NOTEBOOKS[i].filename;
            info.name = info.filename.substr(0, info.filename.size() - 3); // remove .jl
            info.full_path = full_path;
            info.category = PRECONFIGURED_NOTEBOOKS[i].category;
            info.is_custom = false;
            info.requires_rcall = RequiresRCall(info.filename);
            result.push_back(info);
        }
    }

    // Scan root notebooks directory for any .jl, .R, .py NOT in the preconfigured list.
    // This allows users to drop notebooks directly in C:\NEVEN\notebooks
    {
        WIN32_FIND_DATAA find_data;
        std::string search = notebooks_dir + "*.*";
        HANDLE hFind = FindFirstFileA(search.c_str(), &find_data);
        if (hFind != INVALID_HANDLE_VALUE) {
            do {
                if (!(find_data.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY)) {
                    std::string fname = find_data.cFileName;
                    // Check extension: .jl, .R, .r, .py
                    std::string ext = "";
                    size_t dot_pos = fname.rfind('.');
                    if (dot_pos != std::string::npos) {
                        ext = fname.substr(dot_pos);
                    }
                    bool is_notebook = (ext == ".jl" || ext == ".R" || ext == ".r" || ext == ".py");
                    if (!is_notebook) continue;

                    // Skip if already in preconfigured list
                    bool already_listed = false;
                    for (const auto& existing : result) {
                        if (existing.filename == fname) { already_listed = true; break; }
                    }
                    if (!already_listed) {
                        NotebookInfo info;
                        info.filename = fname;
                        info.name = fname.substr(0, dot_pos);
                        info.full_path = notebooks_dir + fname;
                        // Categorize by extension
                        if (ext == ".jl") info.category = "Julia";
                        else if (ext == ".R" || ext == ".r") info.category = "R";
                        else if (ext == ".py") info.category = "Python";
                        info.is_custom = true;
                        info.requires_rcall = (ext == ".R" || ext == ".r");
                        result.push_back(info);
                    }
                }
            } while (FindNextFileA(hFind, &find_data));
            FindClose(hFind);
        }
    }

    // Scan custom notebooks directory (notebooks/custom/) for .jl, .R, .py
    {
        std::string custom_patterns[] = {"*.jl", "*.py", "*.R"};
        for (int ci = 0; ci < 3; ci++) {
            WIN32_FIND_DATAA cfd;
            std::string csearch = custom_dir + custom_patterns[ci];
            HANDLE hFind2 = FindFirstFileA(csearch.c_str(), &cfd);
            if (hFind2 != INVALID_HANDLE_VALUE) {
                do {
                    if (!(cfd.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY)) {
                        std::string fname = cfd.cFileName;
                        // Skip if already listed
                        bool already_listed = false;
                        for (const auto& existing : result) {
                            if (existing.filename == fname) { already_listed = true; break; }
                        }
                        if (!already_listed) {
                            NotebookInfo info;
                            info.filename = fname;
                            auto dot_pos = fname.rfind('.');
                            info.name = (dot_pos != std::string::npos) ? fname.substr(0, dot_pos) : fname;
                            info.full_path = custom_dir + fname;
                            std::string fext = (dot_pos != std::string::npos) ? fname.substr(dot_pos) : "";
                            if (fext == ".jl") info.category = "Custom (Julia)";
                            else if (fext == ".py") info.category = "Custom (Python)";
                            else if (fext == ".R") info.category = "Custom (R)";
                            else info.category = "Custom";
                            info.is_custom = true;
                            info.requires_rcall = (fext == ".R");
                            result.push_back(info);
                        }
                    }
                } while (FindNextFileA(hFind2, &cfd));
                FindClose(hFind2);
            }
        }
    }

    return result;
}

// ─── Formatted Listing ──────────────────────────────────────────────────

std::string NotebookLibrary::ListNotebooksFormatted() const {
    auto notebooks = ListNotebooks();
    std::stringstream ss;
    for (size_t i = 0; i < notebooks.size(); i++) {
        if (i > 0) ss << ", ";
        ss << notebooks[i].name;
        if (notebooks[i].is_custom) ss << " [custom]";
    }
    return ss.str();
}

// ─── Lookup ─────────────────────────────────────────────────────────────

NotebookLibrary::NotebookInfo NotebookLibrary::FindNotebook(const std::string& notebook_name) const {
    auto notebooks = ListNotebooks();

    // Search by name (without .jl extension)
    for (const auto& nb : notebooks) {
        if (nb.name == notebook_name || nb.filename == notebook_name) {
            return nb;
        }
    }

    // Not found
    NotebookInfo empty;
    empty.name = "";
    return empty;
}

bool NotebookLibrary::NotebookExists(const std::string& notebook_name) const {
    auto info = FindNotebook(notebook_name);
    return !info.name.empty();
}

// ─── Classification ─────────────────────────────────────────────────────

bool NotebookLibrary::RequiresRCall(const std::string& filename) {
    // Check against preconfigured registry
    for (int i = 0; i < PRECONFIGURED_COUNT; i++) {
        if (filename == PRECONFIGURED_NOTEBOOKS[i].filename) {
            std::string cat = PRECONFIGURED_NOTEBOOKS[i].category;
            return cat == "R via RCall" || cat == "Mixed R+Julia";
        }
    }
    return false;  // Unknown notebooks don't require RCall by default
}

} // namespace rj2xcl
