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
#include "Julia_Environment.h"
#include <windows.h>
#include <iostream>
#include "JuliaConversion.h"

namespace rj2xcl {

Julia_Environment::Julia_Environment() : m_initialized(false) {
}

Julia_Environment::~Julia_Environment() {
    Shutdown();
}

bool Julia_Environment::Initialize(const std::string& homePaths) {
    if (m_initialized) return true;

    // Default to the shared system library if no path is given
    std::string jlDllPath = homePaths.empty() ? "libjulia.dll" : homePaths + "\\bin\\libjulia.dll";

    HMODULE lib = LoadLibraryA(jlDllPath.c_str());
    if(!lib) {
        std::cerr << "Julia_Environment::Initialize - Failed to load libjulia.dll at " << jlDllPath << std::endl;
        return false;
    }

    typedef void(*p_jl_init_t)(void);
    p_jl_init_t p_jl_init = (p_jl_init_t)GetProcAddress(lib, "jl_init__threading");
    
    // Fallback to legacy single thread init
    if(!p_jl_init) {
        p_jl_init = (p_jl_init_t)GetProcAddress(lib, "jl_init");
    }

    if(!p_jl_init) {
        std::cerr << "Julia_Environment::Initialize - Valid jl_init function not found in libjulia.dll" << std::endl;
        FreeLibrary(lib);
        return false;
    }

    // Initialize the Julia engine
    p_jl_init();
    
    m_initialized = true;
    return true;
}

void Julia_Environment::Shutdown() {
    if (!m_initialized) return;
    
    // Call julia's exit hooks here (e.g. jl_atexit_hook(0))
    m_initialized = false;
}

bool Julia_Environment::ExecuteString(const std::string& code) {
    if (!m_initialized) return false;
    
    // Call jl_eval_string(code) and check jl_exception_occurred()
    // return jl_exception_occurred() == nullptr;
    return true; 
}

xloper12* Julia_Environment::CallFunction(const std::string& functionName, const std::vector<xloper12*>& args) {
    if (!m_initialized) return nullptr;
    
    // Data Bridging:
    std::vector<jl_value_t*> jl_args;
    for(const auto& arg : args) {
        jl_args.push_back(julia_mapper::xloper12_to_jl_value(arg));
    }
    
    // 2. Locate function symbol via jl_get_function(jl_main_module, name)
    // 3. Apply arguments: jl_call(function_ptr, args_ptr, nargs)
    
    // Mock result handling
    jl_value_t* result_mock = nullptr; // In reality: jl_call(...)
    
    // 4. Transform result jl_value_t back to allocated xloper12
    return julia_mapper::jl_value_to_xloper12(result_mock);
}

void Julia_Environment::ForceGarbageCollection() {
    if (!m_initialized) return;
    
    // Call jl_gc_collect(JL_GC_FULL) mapping dynamically resolved handle
    // p_jl_gc_collect(1); 
}

} // namespace rj2xcl
