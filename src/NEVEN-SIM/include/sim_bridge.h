/**
 * @file sim_bridge.h
 * @brief SimBridge — discovers and communicates with NEVEN base engines.
 *
 * Phase 1: Uses xlUDF relay to call NEVEN.r() and NEVEN.j() functions.
 * Phase 2: Direct Named Pipe connections (future).
 *
 * Copyright (c) 2026 NEVEN Project — GPL v3
 */

#pragma once

#include <string>
#include <mutex>
#include "XLCALL.H"

namespace neven_sim {

/**
 * @brief Singleton that bridges NEVEN-SIM to the NEVEN base engines.
 *
 * Discovers whether NEVEN64.xll is loaded and provides methods to
 * execute R and Julia code through the base add-in's existing infrastructure.
 */
class SimBridge {
public:
    static SimBridge& Instance();

    /**
     * @brief Initialize the bridge — detect NEVEN base availability.
     * @return true if NEVEN64.xll is loaded and responsive.
     */
    bool Initialize();

    /**
     * @brief Check if NEVEN base is available for calls.
     * @return true if base XLL is loaded.
     */
    bool IsBaseAvailable() const { return base_available_; }

    /**
     * @brief Lazy re-detection of NEVEN base. Call this before any engine call
     *        in case NEVEN64.xll loaded after NEVEN-SIM.xll.
     * @return true if base XLL is now available.
     */
    bool EnsureAvailable();

    /**
     * @brief Execute R code via NEVEN.r() and return the result as string.
     * @param code R code to execute.
     * @return Result string, or error message prefixed with "[ERROR]".
     */
    std::string CallR(const std::string& code);

    /**
     * @brief Execute Julia code via NEVEN.j() and return the result as string.
     * @param code Julia code to execute.
     * @return Result string, or error message prefixed with "[ERROR]".
     */
    std::string CallJulia(const std::string& code);

    /**
     * @brief Execute R code and return raw XLOPER12 result (caller frees).
     * @param code R code to execute.
     * @param result Output XLOPER12 populated with the result.
     * @return true on success.
     */
    bool CallR_Raw(const std::string& code, XLOPER12& result);

    /**
     * @brief Execute Julia code and return raw XLOPER12 result (caller frees).
     * @param code Julia code to execute.
     * @param result Output XLOPER12 populated with the result.
     * @return true on success.
     */
    bool CallJulia_Raw(const std::string& code, XLOPER12& result);

    /**
     * @brief Returns the NEVEN home directory (typically C:\NEVEN).
     */
    std::string GetHomePath() const { return home_path_; }

    /**
     * @brief Call any NEVEN base function via xlUDF (public wrapper).
     * @param func_name Function name (e.g., "NEVEN.v").
     * @param arg String argument to pass.
     * @param result Output XLOPER12.
     * @return true on success.
     */
    bool CallUDF_Public(const std::string& func_name, const std::string& arg, XLOPER12& result);

private:
    SimBridge();
    ~SimBridge() = default;
    SimBridge(const SimBridge&) = delete;
    SimBridge& operator=(const SimBridge&) = delete;

    bool DetectNevenBase();
    bool CallUDF(const std::string& func_name, const std::string& code, XLOPER12& result);

    bool base_available_ = false;
    std::string home_path_;
    mutable std::mutex mutex_;
};

} // namespace neven_sim
