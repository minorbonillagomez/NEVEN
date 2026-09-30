/**
 * Copyright (c) 2026 RJ2XCL Project — GPL v3
 *
 * @file REPLLanguageAccessor.h
 * @brief Abstract interface for REPL access to language services.
 *
 * This decouples the Common library (REPLBridge) from the Core library
 * (LanguageManager). The Core library provides the concrete implementation
 * and registers it at startup.
 */

#pragma once

#include <string>

namespace rj2xcl {

/**
 * @brief Interface for REPL access to language services.
 *
 * Implemented in Core and registered with REPLBridge at startup.
 * This avoids a circular dependency between Common and Core.
 */
class REPLLanguageAccessor {
public:
    virtual ~REPLLanguageAccessor() = default;

    /** @brief Check if a language name is registered. */
    virtual bool IsLanguageRegistered(const std::string& name) const = 0;

    /** @brief Check if a language service is connected. */
    virtual bool IsLanguageConnected(const std::string& name) const = 0;

    /**
     * @brief Execute a shell command in the specified language.
     * @param language Language name ("R", "Julia", "Python").
     * @param code Code string to execute.
     * @return Output string from the language engine.
     */
    virtual std::string ExecuteShellCommand(const std::string& language,
                                            const std::string& code) const = 0;

    // ─── Singleton Registration ──────────────────────────────────────────

    /** @brief Register the concrete accessor (called from Core at startup). */
    static void Register(REPLLanguageAccessor* accessor);

    /** @brief Get the registered accessor (nullptr if not registered). */
    static REPLLanguageAccessor* Get();

private:
    static REPLLanguageAccessor* instance_;
};

} // namespace rj2xcl
