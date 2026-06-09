#pragma once

#ifndef SANDBOX_VERIFIER_H
#define SANDBOX_VERIFIER_H

#include <string>
#include <vector>

namespace rj2xcl {
namespace security {

enum class ExecutionTrustLevel {
    Trusted,
    PromptUser,
    Blocked
};

/**
 * @brief Execution source for audit trail and logging.
 */
enum class ExecutionSource {
    ExcelCell,      ///< =RJ2XCL.R("...") or =RJ2XCL.J("...") from a cell formula
    REPL,           ///< Console/REPL interactive input
    AutoLoader,     ///< User script directory auto-load at startup
    RegisteredFunc  ///< Pre-loaded registered function
};

/**
 * SandboxVerifier
 * Scans requested bindings and scripts before they reach IScriptEngine.
 * Protects users from malicious auto-execution payloads contained in downloaded workbooks.
 */
class SandboxVerifier {
public:
    static SandboxVerifier& GetInstance();

    // Verify if a snippet of code is safe to execute blindly
    ExecutionTrustLevel EvaluateScript(const std::string& scriptContext);

    /**
     * @brief Validates code before execution against the blocked-pattern list.
     * @param code The code string to validate.
     * @param rejection_reason Output string describing why the code was rejected.
     * @return true if the code is safe to execute, false if blocked.
     */
    bool ValidateCodeForExecution(const std::string& code, std::string& rejection_reason) const;

    /**
     * @brief Validates code for execution from ANY path (cell, REPL, AutoLoader).
     * @param code The code string to validate.
     * @param source Execution source for audit logging.
     * @param rejection_reason Output: reason string if code is blocked.
     * @return true if safe to execute, false if blocked.
     */
    bool ValidateFromAnySource(const std::string& code,
                               ExecutionSource source,
                               std::string& rejection_reason) const;
    
    // Add known trusted hashes or paths
    void AddTrustedSignature(const std::string& signature);

private:
    SandboxVerifier() = default;
    ~SandboxVerifier() = default;

    SandboxVerifier(const SandboxVerifier&) = delete;
    SandboxVerifier& operator=(const SandboxVerifier&) = delete;

    std::vector<std::string> m_trusted_signatures;
    
    bool ContainsRestrictedCommands(const std::string& code) const;

    static const char* ExecutionSourceToString(ExecutionSource source);
};

} // namespace security
} // namespace rj2xcl

#endif // SANDBOX_VERIFIER_H
#pragma once

#ifndef RUNTIMELOADER_H
#define RUNTIMELOADER_H

#include <memory>
#include <string>
#include <stdexcept>
#include "../../include/ScriptEngine.h"

namespace rj2xcl {

/**
 * RuntimeLoader
 * Implements the Lazy Loading Pattern. 
 * Prevents Excel from allocating high-memory runtime processes (R/Julia)
 * until a user explicitly calls a function bound to them.
 */
class RuntimeLoader {
public:
    enum class EngineType {
        R,
        Julia
    };

    static RuntimeLoader& GetInstance();

    // Fetches the engine. If it's not loaded, it initializes it on the fly.
    IScriptEngine* GetEngine(EngineType type, const std::string& homePaths = "");

private:
    RuntimeLoader() = default;
    ~RuntimeLoader() = default;

    RuntimeLoader(const RuntimeLoader&) = delete;
    RuntimeLoader& operator=(const RuntimeLoader&) = delete;

    std::unique_ptr<IScriptEngine> m_r_engine;
    std::unique_ptr<IScriptEngine> m_julia_engine;
};

} // namespace rj2xcl

#endif // RUNTIMELOADER_H
#pragma once

#ifndef GC_MONITOR_H
#define GC_MONITOR_H

#include <vector>
#include <mutex>

namespace rj2xcl {

class IScriptEngine; // Forward declaration

/**
 * GCMonitor
 * Unifies the Garbage Collection strategy between Excel COM threads
 * and the execution instances of R and Julia.
 */
class GCMonitor {
public:
    static GCMonitor& GetInstance();
    
    // Register engines to broadcast memory freeing events
    void RegisterEngine(IScriptEngine* engine);
    
    // Call when Excel completes large COM evaluations
    void NotifyExcelCOMRelease();
    
    // Force aggressive sweep across all mapped runtimes
    void ForceGlobalSweep();

private:
    GCMonitor() = default;
    ~GCMonitor() = default;
    
    // Delete copy/move constructors for Singleton
    GCMonitor(const GCMonitor&) = delete;
    GCMonitor& operator=(const GCMonitor&) = delete;

    std::vector<IScriptEngine*> m_engines;
    std::mutex m_mutex;
    
    int m_excel_allocations_since_sweep = 0;
};

} // namespace rj2xcl

#endif // GC_MONITOR_H
#pragma once

#ifndef AUTOLOADER_H
#define AUTOLOADER_H

#include <string>
#include <vector>

namespace rj2xcl {

/**
 * AutoLoader
 * Scans a predefined user directory (e.g. Documents/RJ2XCL/scripts)
 * Finds any .R or .jl files and executes their content so the user functions
 * are readily available in the Excel environment without manual typing.
 */
class AutoLoader {
public:
    static AutoLoader& GetInstance();

    // Set the base directory to scan. Typically called on xlAutoOpen
    void SetUserScriptDirectory(const std::string& directoryPath);

    // Scan the directory and evaluate all scripts into the respective engines
    void LoadAllUserScripts();

    // Specific loaders exposed for lazy loading compatibility
    void SourcingRFiles();
    void SourcingJuliaFiles();

private:
    AutoLoader() = default;
    ~AutoLoader() = default;

    AutoLoader(const AutoLoader&) = delete;
    AutoLoader& operator=(const AutoLoader&) = delete;

    std::string m_script_directory;

    std::string ReadFileContent(const std::string& filePath) const;
};

} // namespace rj2xcl

#endif // AUTOLOADER_H
