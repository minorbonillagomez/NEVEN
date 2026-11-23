/**
 * Copyright (c) 2026 RJ2XCL Project
 *
 * @file engine_availability.cc
 * @brief Catalog of the language engines NEVEN connects to and the text shown
 *        when one of them is not available.
 */

#include "engine_availability.h"

namespace rj2xcl {

    const char* const kEngineSettingsHint =
        "Active o desactive motores en NEVEN Studio > Settings > Motores (requiere reiniciar Excel).";

    const std::vector<EngineCatalogEntry>& EngineCatalog() {
        static const std::vector<EngineCatalogEntry> catalog = {
            { "R",      "R", "https://cran.r-project.org/bin/windows/base/" },
            { "Julia",  "J", "https://julialang.org/downloads/" },
            { "Python", "P", "https://www.python.org/downloads/" }
        };
        return catalog;
    }

    std::string EngineDownloadUrl(const std::string& name) {
        for (const auto& entry : EngineCatalog()) {
            if (name == entry.name) return entry.download_url;
        }
        return "";
    }

    /** @brief Short ASCII reason for each configuration state. */
    static std::string EngineUnavailableReason(LanguageConfigState state) {
        switch (state) {
        case LanguageConfigState::NotInConfig:
            return "no esta declarado en neven-config.json";
        case LanguageConfigState::DisabledByUser:
            return "esta desactivado por el usuario (enabled: false)";
        case LanguageConfigState::NotFound:
            return "no se encontro una instalacion en este equipo";
        default:
            return "no esta conectado";
        }
    }

    std::string EngineUnavailableMessage(const std::string& name, LanguageConfigState state) {
        std::string message = name + " no esta disponible: " + EngineUnavailableReason(state) + ".";
        message += " NEVEN no instala motores.";

        std::string url = EngineDownloadUrl(name);
        if (!url.empty()) {
            message += " Descargue " + name + " de " + url;
            message += " y active el motor en NEVEN Studio > Settings > Motores (requiere reiniciar Excel).";
        }
        else {
            message += " ";
            message += kEngineSettingsHint;
        }

        return message;
    }

} // namespace rj2xcl
