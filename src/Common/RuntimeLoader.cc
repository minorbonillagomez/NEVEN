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

#include "RuntimeLoader.h"
#include "../ControlR/include/R_Environment.h"
#include "../ControlJulia/include/Julia_Environment.h"
#include "../include/AutoLoader.h"
#include <iostream>

namespace rj2xcl {

RuntimeLoader& RuntimeLoader::GetInstance() {
    static RuntimeLoader instance;
    return instance;
}

IScriptEngine* RuntimeLoader::GetEngine(EngineType type, const std::string& homePaths) {
    switch(type) {
        case EngineType::R:
            if (!m_r_engine) {
                std::cout << "[RuntimeLoader] Lazy-loading R Environment..." << std::endl;
                m_r_engine = std::make_unique<R_Environment>();
                if (!m_r_engine->Initialize(homePaths)) {
                    throw std::runtime_error("Failed to initialize R Environment lazy loading.");
                }
                // Source custom user scripts immediately after boot
                AutoLoader::GetInstance().SourcingRFiles();
            }
            return m_r_engine.get();

        case EngineType::Julia:
            if (!m_julia_engine) {
                std::cout << "[RuntimeLoader] Lazy-loading Julia Environment..." << std::endl;
                m_julia_engine = std::make_unique<Julia_Environment>();
                if (!m_julia_engine->Initialize(homePaths)) {
                    throw std::runtime_error("Failed to initialize Julia Environment lazy loading.");
                }
                // Source custom user scripts immediately after boot
                AutoLoader::GetInstance().SourcingJuliaFiles();
            }
            return m_julia_engine.get();

        default:
            return nullptr;
    }
}

} // namespace rj2xcl
