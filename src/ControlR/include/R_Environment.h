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

#ifndef R_ENVIRONMENT_H
#define R_ENVIRONMENT_H

#include "../../include/ScriptEngine.h"

namespace rj2xcl {

/**
 * R_Environment
 * Concrete implementation of the IScriptEngine for R (version > 3.5).
 * Connects to R.dll dynamically and maps the engine lifecycle and evaluation calls.
 */
class R_Environment : public IScriptEngine {
public:
    R_Environment();
    ~R_Environment() override;

    bool Initialize(const std::string& homePaths) override;
    void Shutdown() override;

    bool ExecuteString(const std::string& code) override;
    
    xloper12* CallFunction(const std::string& functionName, const std::vector<xloper12*>& args) override;

    void ForceGarbageCollection() override;

private:
    bool m_initialized;
    // Pointers to dynamic functions from R.dll will reside here
    
    // Internal helper for R's dynamic string conversions (handling UTF-8 in R 4.x)
    void ConfigureUTF8Locale();
};

} // namespace rj2xcl

#endif // R_ENVIRONMENT_H
