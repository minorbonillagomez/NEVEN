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

#include "AutoLoader.h"
#include "RuntimeLoader.h"
#include "SandboxVerifier.h"
#include "LogService.h"
#include <filesystem>
#include <fstream>
#include <sstream>
#include <iostream>

namespace fs = std::filesystem;

namespace rj2xcl {

AutoLoader& AutoLoader::GetInstance() {
    static AutoLoader instance;
    return instance;
}

void AutoLoader::SetUserScriptDirectory(const std::string& directoryPath) {
    m_script_directory = directoryPath;
    
    // Create the directory if it doesn't exist
    if (!fs::exists(m_script_directory)) {
        try {
            fs::create_directories(m_script_directory);
        } catch(const std::exception& e) {
            std::cerr << "[AutoLoader] Failed to create script directory: " << e.what() << std::endl;
        }
    }
}

void AutoLoader::LoadAllUserScripts() {
    if (m_script_directory.empty() || !fs::exists(m_script_directory)) return;

    std::cout << "[AutoLoader] Scanning directory for user scripts: " << m_script_directory << std::endl;

    SourcingRFiles();
    SourcingJuliaFiles();
}

std::string AutoLoader::ReadFileContent(const std::string& filePath) const {
    std::ifstream file(filePath);
    if (!file.is_open()) return "";
    
    std::stringstream buffer;
    buffer << file.rdbuf();
    return buffer.str();
}

void AutoLoader::SourcingRFiles() {
    auto engine = RuntimeLoader::GetInstance().GetEngine(RuntimeLoader::EngineType::R);
    if (!engine) return;

    auto& sandbox = security::SandboxVerifier::GetInstance();

    for (const auto& entry : fs::directory_iterator(m_script_directory)) {
        if (entry.is_regular_file() && entry.path().extension() == ".R") {
            std::string content = ReadFileContent(entry.path().string());
            if (!content.empty()) {
                std::string rejection_reason;
                if (!sandbox.ValidateFromAnySource(content,
                        security::ExecutionSource::AutoLoader,
                        rejection_reason)) {
                    RJ2XCL_LOG_WARN("[AutoLoader] Blocked: %s — %s",
                        entry.path().filename().string().c_str(),
                        rejection_reason.c_str());
                    continue;
                }
                std::cout << "[AutoLoader] Sourcing R file: " << entry.path().filename() << std::endl;
                engine->ExecuteString(content);
            }
        }
    }
}

void AutoLoader::SourcingJuliaFiles() {
    auto engine = RuntimeLoader::GetInstance().GetEngine(RuntimeLoader::EngineType::Julia);
    if (!engine) return;

    auto& sandbox = security::SandboxVerifier::GetInstance();

    for (const auto& entry : fs::directory_iterator(m_script_directory)) {
        if (entry.is_regular_file() && entry.path().extension() == ".jl") {
            std::string content = ReadFileContent(entry.path().string());
            if (!content.empty()) {
                std::string rejection_reason;
                if (!sandbox.ValidateFromAnySource(content,
                        security::ExecutionSource::AutoLoader,
                        rejection_reason)) {
                    RJ2XCL_LOG_WARN("[AutoLoader] Blocked: %s — %s",
                        entry.path().filename().string().c_str(),
                        rejection_reason.c_str());
                    continue;
                }
                std::cout << "[AutoLoader] Sourcing Julia file: " << entry.path().filename() << std::endl;
                engine->ExecuteString(content);
            }
        }
    }
}

} // namespace rj2xcl
