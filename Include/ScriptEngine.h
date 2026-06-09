#pragma once

#ifndef SCRIPT_ENGINE_H
#define SCRIPT_ENGINE_H

#include <string>
#include <vector>

// Forward declarations for Excel types (simplified for interface)
struct xloper12;

namespace rj2xcl {

/**
 * Universal interface for Scripting Engines (R, Julia, etc.)
 * This isolates Excel-specific logic from language runtimes.
 */
class IScriptEngine {
public:
    virtual ~IScriptEngine() = default;

    // Initialization and lifecycle
    virtual bool Initialize(const std::string& homePaths) = 0;
    virtual void Shutdown() = 0;

    // Execution
    virtual bool ExecuteString(const std::string& code) = 0;
    
    // Data Bridging
    // Converts data from Excel (xloper12) to the engine's internal format, executes a function, and returns xloper12
    virtual xloper12* CallFunction(const std::string& functionName, const std::vector<xloper12*>& args) = 0;

    // Garbage Collection Coordination
    virtual void ForceGarbageCollection() = 0;
};

} // namespace rj2xcl

#endif // SCRIPT_ENGINE_H
