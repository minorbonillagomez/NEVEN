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

#pragma once

#include <vector>
#include <memory>
#include "language_service.h"
#include "callback_info.h"
#include "com_object_map.h"
#include "variable.pb.h"
#include "json11/json11.hpp"

namespace rj2xcl {

    /**
     * @brief Dynamic registry for scripting language services.
     *
     * LanguageManager acts as a central registry and lifecycle manager for all
     * language services (R, Julia, and potentially future languages like Python).
     * It follows the Singleton pattern to ensure a single point of orchestration.
     *
     * @par Design Pattern
     * Service Registry + Singleton. Adding a new language requires implementing
     * a LanguageService subclass — no changes to LanguageManager or the Excel bridge.
     */
    class LanguageManager {
    public:
        /** @brief Returns the singleton instance. */
        static LanguageManager& Instance();

        /**
         * @brief Resets the singleton instance state for unit testing isolation.
         * @note Only intended to be called from the test suite.
         */
        void ResetForTesting();

        /** @brief Gracefully shuts down all language services and releases resources. */
        void Shutdown();

        /**
         * @brief Retrieves a language service by its numeric key.
         * @param key Internal index assigned during ConfigureLanguages.
         * @return Shared pointer to the service, or nullptr if not found.
         */
        std::shared_ptr<LanguageService> GetLanguageService(uint32_t key);

        /**
         * @brief Retrieves a language service by its display name.
         * @param name Language name (e.g., "R", "Julia").
         * @return Shared pointer to the service, or nullptr if not found.
         */
        std::shared_ptr<LanguageService> GetLanguageService(const std::string &name);

        /**
         * @brief Dispatches a function call to the specified language engine.
         * @param language_key Numeric key identifying the target language.
         * @param response Protobuf response to populate with the result.
         * @param call Protobuf call containing function name and arguments.
         */
        void CallLanguage(uint32_t language_key, RJ2XCLBuffers::CallResponse &response, RJ2XCLBuffers::CallResponse &call);

        /** @brief Registers all language function descriptors with Excel's function wizard. */
        void RegisterLanguageCalls();

        /**
         * @brief Phase 1: Configures language services from JSON settings.
         * @param dev_flags Developer option flags from the registry.
         * @param config Main application configuration JSON.
         * @param home_directory RJ2XCL installation home path.
         * @param language_config Language-specific configuration (rj2xcl-languages.json).
         * @param callback_info Callback info shared with the Excel bridge.
         * @param object_map COM object map for Excel automation.
         */
        void ConfigureLanguages(DWORD dev_flags, const json11::Json& config, const std::string& home_directory, const json11::Json& language_config, CallbackInfo& callback_info, COMObjectMap& object_map);

        /**
         * @brief Phase 2: Starts language processes and connects Named Pipes.
         * @param job_handle Windows Job Object handle for child process management.
         */
        void ConnectLanguages(HANDLE job_handle);

        /** @brief Phase 3: Sends initialization commands to connected engines. */
        void InitializeConnectedLanguages();

        /** @brief Returns a read-only reference to the registered language services. */
        const std::vector<std::shared_ptr<LanguageService>>& GetServices() const { return language_services_; }

    private:
        LanguageManager() = default;
        ~LanguageManager() = default;
        LanguageManager(const LanguageManager&) = delete;
        LanguageManager& operator=(const LanguageManager&) = delete;

        std::vector<std::shared_ptr<LanguageService>> language_services_;
    };

} // namespace rj2xcl
