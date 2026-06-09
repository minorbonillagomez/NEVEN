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
#pragma once

#ifndef JULIA_ENVIRONMENT_H
#define JULIA_ENVIRONMENT_H

#include "../../include/ScriptEngine.h"

namespace rj2xcl {

/**
 * Julia_Environment
 * Concrete implementation of the IScriptEngine for Julia execution.
 * Intended to be backward and forward compatible.
 */
class Julia_Environment : public IScriptEngine {
public:
    Julia_Environment();
    ~Julia_Environment() override;

    bool Initialize(const std::string& homePaths) override;
    void Shutdown() override;

    bool ExecuteString(const std::string& code) override;
    
    xloper12* CallFunction(const std::string& functionName, const std::vector<xloper12*>& args) override;

    void ForceGarbageCollection() override;

private:
    bool m_initialized;
    // Pointers for julia C API: (jl_eval_string, jl_init, jl_atexit_hook, jl_gc_collect)
};

} // namespace rj2xcl

#endif // JULIA_ENVIRONMENT_H
