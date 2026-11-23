/**
 * Copyright (c) 2026 RJ2XCL Project
 *
 * This file is part of RJ2XCL.
 *
 * RJ2XCL is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 */

#pragma once

#include <string>
#include <vector>

namespace rj2xcl {

    /**
     * @brief Why a language engine did not end up configured.
     *
     * Lives in Common so that both Core (LanguageService, LanguageManager,
     * basic_functions) and Common (PlutoManager) can report the reason without
     * Common depending on Core.
     */
    enum class LanguageConfigState {
        Configured,      ///< Declared, enabled and discovered on this machine
        NotInConfig,     ///< No section for the language in neven-config.json
        DisabledByUser,  ///< Section present with "enabled": false
        NotFound         ///< Enabled, but no installation was discovered
    };

    /** @brief One entry of the catalog of engines NEVEN knows how to connect to. */
    struct EngineCatalogEntry {
        const char* name;          ///< Display name ("R", "Julia", "Python")
        const char* prefix;        ///< Excel formula prefix ("R", "J", "P")
        const char* download_url;  ///< Official HTTPS download page
    };

    /**
     * @brief Returns the three engines NEVEN connects to.
     *
     * The URLs are the ones the installer already uses (Install-NEVEN.ps1).
     * NEVEN never installs, downloads or bundles a third party runtime: it only
     * reports what is missing and links to the official page.
     */
    const std::vector<EngineCatalogEntry>& EngineCatalog();

    /**
     * @brief Returns the official download page of an engine.
     * @param name Engine display name.
     * @return URL, or an empty string if the name is not in the catalog.
     */
    std::string EngineDownloadUrl(const std::string& name);

    /**
     * @brief Builds the message shown when an engine is not available.
     *
     * ASCII only (no accents, no em-dash) because it is returned into an Excel
     * cell and into the Ribbon status text.
     *
     * @param name Engine display name.
     * @param state Why the engine is not available.
     * @return Reason, the "NEVEN does not install engines" note, the official
     *         URL and where the user turns the engine on.
     */
    std::string EngineUnavailableMessage(const std::string& name, LanguageConfigState state);

    /** @brief Where the user changes which engines are active (INV-CMN-01). */
    extern const char* const kEngineSettingsHint;

} // namespace rj2xcl
