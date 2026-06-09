/**
 * Copyright (c) 2026 RJ2XCL Project — GPL v3
 *
 * @file REPLManager.h
 * @brief Singleton managing the WebView2 REPL console lifecycle.
 *
 * Replaces the Electron-based console with a lightweight REPL running
 * inside the existing WebView2 viewer subsystem. Manages command history,
 * language tab state, and viewer window lifecycle.
 */

#pragma once

#include <string>
#include <deque>
#include <unordered_map>
#include <mutex>

namespace rj2xcl {

/**
 * @brief Singleton that manages the WebView2 REPL console.
 *
 * Lifecycle:
 *   1. ShowConsole() — create or bring-to-front the REPL viewer window
 *   2. HideConsole() — hide the viewer and return focus to Excel
 *   3. Shutdown() — close viewer, clear state (called from xlAutoClose)
 *
 * Command history is stored per-language in memory (session-scoped).
 */
class REPLManager {
public:
    static REPLManager& Instance();

    // ─── Console Lifecycle ───────────────────────────────────────────────

    /**
     * @brief Open or bring-to-front the REPL console window.
     * @return Viewer identifier string or error string.
     */
    std::string ShowConsole();

    /**
     * @brief Hide the REPL console window and return focus to Excel.
     */
    void HideConsole();

    /**
     * @brief Close the REPL console and release resources.
     * Called from xlAutoClose via WindowManager::ShutdownConsole().
     */
    void Shutdown();

    /**
     * @brief Returns true if the REPL console window is currently open.
     */
    bool IsConsoleOpen() const;

    /**
     * @brief Get the viewer_id of the REPL console (empty if not open).
     */
    std::string GetConsoleViewerId() const;

    // ─── Command History ─────────────────────────────────────────────────

    /**
     * @brief Store a command in history for a language.
     * Skips consecutive duplicates and enforces the 500-entry cap.
     * @param language Language name ("R", "Julia", "Python").
     * @param command The command string to store.
     */
    void AddToHistory(const std::string& language, const std::string& command);

    /**
     * @brief Get command history for a language.
     * @param language Language name.
     * @return Reference to the command deque (most recent at back).
     */
    const std::deque<std::string>& GetHistory(const std::string& language) const;

    // ─── Active Language Tab ─────────────────────────────────────────────

    /**
     * @brief Get the last active language tab name.
     * @return Language name string (defaults to "R").
     */
    std::string GetLastActiveLanguage() const;

    /**
     * @brief Set the last active language tab name.
     * @param language Language name.
     */
    void SetLastActiveLanguage(const std::string& language);

private:
    REPLManager();
    ~REPLManager();
    REPLManager(const REPLManager&) = delete;
    REPLManager& operator=(const REPLManager&) = delete;

    // ─── Command History Data ────────────────────────────────────────────

    /**
     * @brief Per-language command history with bounded buffer.
     */
    struct LanguageHistory {
        std::deque<std::string> commands;
        static constexpr size_t MAX_HISTORY = 500;

        /**
         * @brief Add a command to history.
         * Skips consecutive duplicates and enforces the size cap.
         */
        void Add(const std::string& cmd) {
            if (cmd.empty()) return;
            // Skip duplicate consecutive commands
            if (!commands.empty() && commands.back() == cmd) return;
            if (commands.size() >= MAX_HISTORY) commands.pop_front();
            commands.push_back(cmd);
        }
    };

    // ─── State ───────────────────────────────────────────────────────────

    std::string console_viewer_id_;
    std::string last_active_language_;
    std::unordered_map<std::string, LanguageHistory> history_;
    mutable std::mutex mutex_;

    /// Empty deque returned when no history exists for a language.
    static const std::deque<std::string> empty_history_;
};

} // namespace rj2xcl
