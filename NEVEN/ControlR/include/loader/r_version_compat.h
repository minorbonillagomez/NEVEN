/**
 * Copyright (c) 2026 RJ2XCL Project
 *
 * r_version_compat.h — NEVEN v2.4 Runtime Version Compatibility
 *
 * Public interface for applying version-specific adaptations to the R
 * startup configuration.  All implementation is in r_version_compat.cc.
 */

#pragma once

#include "r_engine_loader.h"

/**
 * @brief Utility class for R version compatibility.
 *
 * All methods are static; no instances should be created.
 */
class RVersionCompat {
public:
    /**
     * @brief Set the ReadConsole callback in Rp to the correct function
     *        signature for the currently loaded R version.
     *
     * Call this after REngineLoader::Load() and after constructing the
     * REngineRstart struct, before passing it to R_SetParams().
     *
     * @param Rp  Pointer to the startup params struct to configure.
     */
    static void ApplyReadConsoleCallback(REngineRstart Rp);

    /**
     * @brief Verify that structRstart layout is compatible with this R version.
     *
     * Currently a no-op for R 4.x–4.6.x.  Will need implementation if a
     * future R version restructures the startup struct.
     *
     * @return true if compatible; false if a fatal layout mismatch is detected.
     */
    static bool ValidateStartupStruct();

    RVersionCompat() = delete;
};
