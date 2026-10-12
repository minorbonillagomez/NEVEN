/**
 * Copyright (c) 2026 RJ2XCL Project
 *
 * This file is part of RJ2XCL.
 *
 * RJ2XCL is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * RJ2XCL is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with RJ2XCL.  If not, see <http://www.gnu.org/licenses/>.
 */
#include "R_Environment.h"
#include <windows.h>
#include <iostream>

namespace rj2xcl {

R_Environment::R_Environment() : m_initialized(false) {
}

R_Environment::~R_Environment() {
    Shutdown();
}

bool R_Environment::Initialize(const std::string& homePaths) {
    if (m_initialized) return true;

    // Use specific path or fallback to System R.dll assuming it is in PATH
    std::string rDllPath = homePaths.empty() ? "R.dll" : homePaths + "\\bin\\x64\\R.dll";
    
    HMODULE r_lib = LoadLibraryA(rDllPath.c_str());
    if(!r_lib) {
        std::cerr << "R_Environment::Initialize - Failed to load R.dll at " << rDllPath << std::endl;
        return false;
    }

    // Explicitly grab core R functions to initialize the engine
    typedef int (*p_Rf_initEmbeddedR_t)(int argc, char **argv);
    p_Rf_initEmbeddedR_t p_Rf_initEmbeddedR = (p_Rf_initEmbeddedR_t)GetProcAddress(r_lib, "Rf_initEmbeddedR");

    if(!p_Rf_initEmbeddedR) {
        std::cerr << "R_Environment::Initialize - Rf_initEmbeddedR not found in R.dll" << std::endl;
        FreeLibrary(r_lib);
        return false;
    }

    char* argv[] = { (char*)"rj2xcl", (char*)"--gui=none", (char*)"--silent" };
    int res = p_Rf_initEmbeddedR(3, argv);
    
    if (res < 0) {
        std::cerr << "R_Environment::Initialize - Rf_initEmbeddedR failed with code " << res << std::endl;
        FreeLibrary(r_lib);
        return false;
    }

    ConfigureUTF8Locale();
    m_initialized = true;
    return true;
}

void R_Environment::Shutdown() {
    if (!m_initialized) return;
    
    // R_dot_Last() / Rf_endEmbeddedR(0) equivalents
    m_initialized = false;
}

bool R_Environment::ExecuteString(const std::string& code) {
    if (!m_initialized) return false;
    // R_tryEval equivalent
    return true; // Simplified for the architectural skeleton
}

xloper12* R_Environment::CallFunction(const std::string& functionName, const std::vector<xloper12*>& args) {
    if (!m_initialized) return nullptr;
    // Convert xloper12 args -> SEXP
    // Call function
    // Convert result SEXP -> xloper12 using UTF-8 awareness
    return nullptr;
}

void R_Environment::ForceGarbageCollection() {
    if (!m_initialized) return;
    // Execute R GC
    ExecuteString("gc()");
}

void R_Environment::ConfigureUTF8Locale() {
    // For R 4.2+, native Windows encoding is UTF-8. 
    // We enforce the C runtime locale to align with R internals.
    setlocale(LC_ALL, ".UTF-8");
}

} // namespace rj2xcl
