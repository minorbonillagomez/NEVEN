/**
 * Copyright (c) 2026 RJ2XCL Project — GPL v3
 *
 * @file NotebookLibrary.h
 * @brief Manages the collection of preconfigured and custom Pluto notebooks.
 */

#pragma once

#include <string>
#include <vector>

namespace rj2xcl {

/**
 * @brief Manages Pluto.jl notebook discovery and classification.
 *
 * Notebooks are stored in:
 *   %RJ2XCL_HOME%/notebooks/         — 13 preconfigured templates
 *   %RJ2XCL_HOME%/notebooks/custom/  — User-modified copies
 *   %RJ2XCL_HOME%/notebooks/exports/ — Exported analysis notebooks
 */
class NotebookLibrary {
public:
    struct NotebookInfo {
        std::string name;           // e.g., "stats_regression"
        std::string filename;       // e.g., "stats_regression.jl"
        std::string full_path;      // Absolute path
        std::string category;       // "R via RCall", "Julia native", "Mixed R+Julia"
        bool is_custom;             // true if from notebooks/custom/
        bool requires_rcall;        // true if notebook uses RCall.jl
    };

    // ─── Discovery ───────────────────────────────────────────────────────

    /** @brief List all available notebooks (preconfigured + custom). */
    std::vector<NotebookInfo> ListNotebooks() const;

    /** @brief Comma-separated list for =RJ2XCL.NOTEBOOK.LIST(). Custom suffixed with [custom]. */
    std::string ListNotebooksFormatted() const;

    // ─── Lookup ──────────────────────────────────────────────────────────

    /** @brief Find a notebook by name. Throws if not found. */
    NotebookInfo FindNotebook(const std::string& notebook_name) const;

    /** @brief Check if a notebook exists. */
    bool NotebookExists(const std::string& notebook_name) const;

    // ─── Paths ───────────────────────────────────────────────────────────

    std::string GetNotebooksDirectory() const;
    std::string GetCustomDirectory() const;
    std::string GetExportsDirectory() const;

    // ─── Classification ──────────────────────────────────────────────────

    /** @brief Returns true if the notebook requires RCall.jl (R via RCall or Mixed). */
    static bool RequiresRCall(const std::string& filename);

private:
    /** @brief Registry of the 13 preconfigured notebooks. */
    struct PreconfiguredEntry {
        const char* filename;
        const char* category;
    };
    static const PreconfiguredEntry PRECONFIGURED_NOTEBOOKS[];
    static const int PRECONFIGURED_COUNT;
};

} // namespace rj2xcl
